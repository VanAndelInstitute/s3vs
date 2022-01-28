''' Lambda function code for processing slide image metadata '''
import os
import json
from urllib.parse import unquote_plus
from datetime import datetime, timezone
import logging
import traceback
import re
from io import BytesIO
import boto3
import openslide
from pylibdmtx import pylibdmtx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROPERTY_NAME_APERIO_IMAGEID = u'aperio.ImageID'
PROPERTY_NAME_APERIO_DATE = u'aperio.Date'
PROPERTY_NAME_APERIO_TIME = u'aperio.Time'
PROPERTY_NAME_APERIO_TZ = u'aperio.Time Zone'
PROPERTY_NAME_APERIO_MPP = u'aperio.MPP'
PROPERTY_NAME_APERIO_APPMAG = u'aperio.AppMag'

SLIDEID_FORMAT = os.environ.get('SLIDEID_FORMAT', r'\w+')
TEXTRACT_THRESHOLD = os.environ.get('TEXTRACT_THRESHOLD', 85)
METADATA_TOPIC_ARN = os.environ.get('METADATA_TOPIC_ARN')
ERROR_TOPIC_ARN = os.environ.get('ERROR_TOPIC_ARN')
if os.environ.get('DEBUG', False):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

def match_id(block):
    ''' Is this line of text a slide ID? '''
    logger.debug('BlockType: %s', block["BlockType"])
    if block['BlockType'] != 'LINE':
        return False
    logger.debug('Text: %s', block["Text"])
    logger.debug('Confidence: %.3f', block["Confidence"])
    if not re.match(SLIDEID_FORMAT, block['Text']):
        return False
    if block['Confidence'] < float(TEXTRACT_THRESHOLD):
        return False
    return True

def lambda_handler(event, _context):
    ''' Given S3 upload event, retrieve the image metadata and publish to SNS topic'''
    logger.debug(json.dumps(event))
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    logger.info('Filename = %s', key)
    try:
        with openslide.OpenSlide(f'/vsis3/{bucket}/{key}') as osr:

            # get image id from tiff tags; create output folder
            image_id = osr.properties.get(PROPERTY_NAME_APERIO_IMAGEID)

            # Extract label and thumbnail images
            label = osr.associated_images.get(u'label').convert('RGB')
            buf = BytesIO()
            label.save(buf, format='JPEG')
            client = boto3.client('textract')
            response = client.detect_document_text(Document={'Bytes': buf.getvalue()})
            # get the first line of text that looks like a valid slide ID
            slide_id = next((block['Text'] for block in response['Blocks'] if match_id(block)),
                            None)
            if not slide_id:
                # decode slide id from 2D Data Matrix barcode in label image
                label_data = pylibdmtx.decode(label)
                if len(label_data) != 1:
                    logger.error('Bad label data')
                    return

                slide_id = label_data[0].data.decode('ascii')
                logger.debug('Barcode data: %s', slide_id)
            label.close()

            # get metadata
            width, height = osr.dimensions
            scan_date = osr.properties.get(PROPERTY_NAME_APERIO_DATE)
            scan_time = osr.properties.get(PROPERTY_NAME_APERIO_TIME)
            scan_timezone = osr.properties.get(PROPERTY_NAME_APERIO_TZ)
            scandate = datetime.strptime(f'{scan_date} {scan_time} {scan_timezone}',
                                        '%m/%d/%y %H:%M:%S %Z%z')
            metadata = json.dumps({
                'Filename': key.strip(),
                'ImageId': int(image_id.strip()),
                'SlideId': slide_id.strip(),
                'width': width,
                'height': height,
                'ScanDate': scandate.isoformat(),
                'MPP': osr.properties.get(PROPERTY_NAME_APERIO_MPP),
                'AppMag': osr.properties.get(PROPERTY_NAME_APERIO_APPMAG),
                'lastModified': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
            })
            logger.debug(metadata)

        # publish metadata
        client = boto3.client('sns')
        response = client.publish(
            TopicArn=METADATA_TOPIC_ARN,
            Message=metadata,
        )
    except Exception:
        client = boto3.client('sns')
        client.publish(
            TopicArn=ERROR_TOPIC_ARN,
            Subject=f'ImportMetadata: error processing {key}',
            Message=traceback.format_exc(),
        )
        raise
