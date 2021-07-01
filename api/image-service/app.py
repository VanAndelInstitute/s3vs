import os
import openslide
from PIL import Image
from PIL import ImageCms
import traceback as tb
import base64
import json
from urllib.parse import urljoin
import re
from io import BytesIO
import logging
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

API_URL = os.environ.get('API_URL')
BUCKET_NAME = os.environ.get('BUCKET_NAME')
FRAME_ANCESTORS = os.environ.get('FRAME_ANCESTORS', "'none'")
ICC_PROFILE_PROPERTY_NAME = 'aperio.ICC Profile'
ICC_AT2 = '/opt/AT2.icm'
ICC_SCANSCOPE = '/opt/ScanScope v1.icm'
ICC_DEST = '/opt/sRGB Color Space Profile.icm'
TILE_SIZE = 720
TILE_QUALITY = 70

open_slides = {}
colorTransforms = {}

def get_best_level_for_downsample(osr, downsample):
    """ Use our own implementation of this since OpenSlide's doesn't handle 
        the slightly-off Aperio SVS values."""
    for i in range(osr.level_count):
        if round(downsample) < round(osr.level_downsamples[i]):
            return 0 if i == 0 else i-1
    return osr.level_count - 1

def respond(success, error=None, status=200, content_type=None):
 
    response = {
        'statusCode': status,
        'body': ''.join(tb.format_exception(type(error), error, error.__traceback__)) if error else success,
        'headers': {
            'Strict-Transport-Security': "max-age=31536000",
            'Content-Security-Policy': f"default-src 'self'; frame-ancestors {FRAME_ANCESTORS}",
            'X-Content-Type-Options': "nosniff",
            'Referrer-Policy': 'same-origin',
        },
    }
    if content_type:
        response['headers']['Content-Type'] = content_type
        if content_type.startswith('image'):
            response['isBase64Encoded'] = True

    log_msg = {x: response[x] if not type(response[x]) is bytes else response[x].decode('ascii') for x in response}
    logger.debug(json.dumps(log_msg))

    return response

def lambda_handler(event, context):
    """ Handler for IIIF protocol requests.
        Returns: an IIIF image, an IIIF info.json response, or a properties.json response."""
    try:
        image_path = event['pathParameters']['imagePath']
        logger.info(image_path)
        # 1001610/info.json
        # 1001610/0,0,2880,2880/720,/0/default.jpg
        match = re.match(r'(?P<image_id>\w+)/((?P<info>(info|properties)\.json)|((?P<assoc>(thumbnail|label))\.jpg)|(?P<region>\d+,\d+,\d+,\d+)/(?P<size>\d*,\d*)/(?P<rotation>\d{1,3})/(?P<quality>color|gray|bitonal|default)\.(?P<format>jpg|tif|png|gif|jp2|pdf|webp))', image_path)
        if not match:
            raise ValueError(f'Bad resource request: {image_path}')

        image_id = match.group('image_id')
        if image_id in open_slides:
            osr = open_slides[image_id]
            colorTransform = colorTransforms[image_id]
        else:
            osr = open_slides[image_id] = openslide.open_slide(f'/vsis3/{BUCKET_NAME}/{image_id}.svs')
            icc_profile_name = osr.properties.get(ICC_PROFILE_PROPERTY_NAME)
            if icc_profile_name == 'AT2':
                source_icc = ImageCms.ImageCmsProfile(ICC_AT2)
            elif icc_profile_name == 'ScanScope v1':
                source_icc = ImageCms.ImageCmsProfile(ICC_SCANSCOPE)
            dest_icc = ImageCms.ImageCmsProfile(ICC_DEST)
            intent = ImageCms.getDefaultIntent(source_icc)
            colorTransform = colorTransforms[image_id] = ImageCms.buildTransform(source_icc, dest_icc, 'RGBA', 'RGBA', intent)

        info_request = match.group('info')
        assoc_request = match.group('assoc')
        if info_request == 'info.json':
            width, height = osr.dimensions
            downsamples = list(map(lambda d: round(d), osr.level_downsamples))
            info = {
                "@context": "http://iiif.io/api/image/2/context.json",
                "@id": urljoin(API_URL, image_id),
                "type": "ImageService3",
                "protocol": "http://iiif.io/api/image",
                "profile": [ "http://iiif.io/api/image/2/level2.json" ],
                "width": width,
                "height": height,
                "tiles": [
                    { "width": TILE_SIZE, "scaleFactors": downsamples }
                ]
            }
            return respond(json.dumps(info), content_type='application/json')
        elif info_request == 'properties.json':
            properties = dict(osr.properties)
            return respond(json.dumps(properties), content_type='application/json')
        elif bool(assoc_request):
            _format = 'jpeg'
            image = osr.associated_images.get(assoc_request).convert('RGB')
            buf = BytesIO()
            image.save(buf, _format, quality=TILE_QUALITY)
            image.close()
            result = buf.getvalue()
        else:
            _format = 'jpeg' if match.group('format') == 'jpg' else _format
            region = match.group('region').split(',')
            x = int(region[0])
            y = int(region[1])
            w = int(region[2])
            h = int(region[3])
            downsample = max(w//TILE_SIZE, h//TILE_SIZE)
            downsamples = list(map(lambda d: round(d), osr.level_downsamples))
            level = get_best_level_for_downsample(osr, downsample)
            size = match.group('size').split(',')
            size = (int(size[0] or size[1]),int(size[1] or size[0]))
            region_size = tuple(l * downsample // downsamples[level] for l in size)
            tile_im = osr.read_region((x,y), level, region_size)
            if tile_im.size != size:
                tile_im.thumbnail(size, Image.ANTIALIAS)
            transformed_im = ImageCms.applyTransform(tile_im, colorTransform)
            tile_im.close()
            converted_im = transformed_im.convert('RGB')
            transformed_im.close()
            buf = BytesIO()
            converted_im.save(buf, _format, quality=TILE_QUALITY)
            converted_im.close()
            result = buf.getvalue()

        return respond(base64.b64encode(result), content_type=f'image/{_format}')
        
    except Exception as e:
        return respond(None, e, 400)
