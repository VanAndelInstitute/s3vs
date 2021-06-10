import os
import json
import boto3
import base64
from botocore.exceptions import ClientError
from urllib.parse import unquote_plus
import openslide
from pylibdmtx import pylibdmtx
from datetime import datetime, timezone
import logging
import requests

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PROPERTY_NAME_APERIO_IMAGEID = u'aperio.ImageID'
PROPERTY_NAME_APERIO_DATE = u'aperio.Date'
PROPERTY_NAME_APERIO_TIME = u'aperio.Time'
PROPERTY_NAME_APERIO_TZ = u'aperio.Time Zone'
PROPERTY_NAME_APERIO_MPP = u'aperio.MPP'
PROPERTY_NAME_APERIO_APPMAG = u'aperio.AppMag'

UPLOAD_URL = os.environ.get('UPLOAD_URL')
SECRET_NAME = os.environ.get('SECRET_NAME')
REGION_NAME = os.environ.get('REGION_NAME')

def get_secret():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=REGION_NAME
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=SECRET_NAME
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))
            

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    logger.info(f'Filename = {key}')
    try:
        osr = openslide.open_slide(f'/vsis3/{bucket}/{key}')
        
        # get image id from tiff tags; create output folder
        image_id = osr.properties.get(PROPERTY_NAME_APERIO_IMAGEID)
        
        # Extract label and thumbnail images
        label = osr.associated_images.get(u'label').convert('RGB')

        # decode slide id from 2D Data Matrix barcode in label image
        label_data = pylibdmtx.decode(label)
        if len(label_data) != 1:
            logger.error('Bad label data')
            return

        slide_id = label_data[0].data.decode('ascii')

        # get metadata
        width, height = osr.dimensions
        scan_date = osr.properties.get(PROPERTY_NAME_APERIO_DATE)
        scan_time = osr.properties.get(PROPERTY_NAME_APERIO_TIME)
        scan_timezone = osr.properties.get(PROPERTY_NAME_APERIO_TZ)
        scandate = datetime.strptime(f'{scan_date} {scan_time} {scan_timezone}', '%m/%d/%y %H:%M:%S %Z%z')
        metadata = {
            # 'Filename': key.strip(),
            'ImageId': image_id.strip(),
            'SlideId': slide_id.strip(),
            # 'width': width,
            # 'height': height,
            # 'ScanDate': scandate.isoformat(),
            # 'MPP': osr.properties.get(PROPERTY_NAME_APERIO_MPP),
            # 'AppMag': osr.properties.get(PROPERTY_NAME_APERIO_APPMAG),
            # 'lastModified': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        }

        # upload metadata
        auth = get_secret()
        x = requests.post(url=UPLOAD_URL, auth=(auth['username'], auth['password']), data=metadata)
        if (x.status_code < 200 | x.status_code >= 400):
            logger.error(f'Metadata upload failed with {x.status_code}: {x.reason}')
        else:
            logger.info(f'Metadata upload responded with {x.status_code}: {x.reason}')
    except Exception as e:
        logger.error(e)
        raise e