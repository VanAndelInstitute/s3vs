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
if (os.environ.get('DEBUG', False)):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

open_slides = {}
colorTransforms = {
    'AT2': None,
    'ScanScope v1': None
}

def get_best_level_for_downsample(osr, downsample):
    """ Use our own implementation of this since OpenSlide's doesn't handle 
        the slightly-off Aperio SVS values."""
    for i in range(osr.level_count):
        if round(downsample) < round(osr.level_downsamples[i]):
            return 0 if i == 0 else i-1
    return osr.level_count - 1

def get_color_transform(icc_profile_name):
    dest_icc = ImageCms.ImageCmsProfile(ICC_DEST)
    if not colorTransforms[icc_profile_name]:
        if icc_profile_name == 'AT2':
            source_icc = ImageCms.ImageCmsProfile(ICC_AT2)
        elif icc_profile_name == 'ScanScope v1':
            source_icc = ImageCms.ImageCmsProfile(ICC_SCANSCOPE)
        else:
            return None
        intent = ImageCms.getDefaultIntent(source_icc)
        colorTransforms[icc_profile_name] = ImageCms.buildTransform(source_icc, dest_icc, 'RGBA', 'RGBA', intent)
    return colorTransforms[icc_profile_name]

def respond(success, error=None, status=200, content_type=None):
 
    if error:
        logger.debug(''.join(tb.format_exception(type(error), error, error.__traceback__)))
    response = {
        'statusCode': status,
        'body': str(error) if error else success,
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

def info_handler(event, context):
    """ Handler for IIIF image information requests.
        Returns: an IIIF info.json response """
    try:
        imageId = event['pathParameters']['imageId']
        logger.info(imageId)
        if imageId in open_slides:
            osr = open_slides[imageId]
        else:
            osr = open_slides[imageId] = openslide.open_slide(f'/vsis3/{BUCKET_NAME}/{imageId}.svs')
        width, height = osr.dimensions
        downsamples = list(map(lambda d: round(d), osr.level_downsamples))
        info = {
            "@context": "http://iiif.io/api/image/2/context.json",
            "@id": urljoin(API_URL, imageId),
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
    except openslide.OpenSlideError:
        return respond(f'Image ID {imageId} not found', None, 404)
    except Exception as e:
        return respond(None, e, 400)

def properties_handler(event, context):
    """ Handler for image properties requests.
        Returns: OpenSlide properties """
    try:
        imageId = event['pathParameters']['imageId']
        logger.info(imageId)
        if imageId in open_slides:
            osr = open_slides[imageId]
        else:
            osr = open_slides[imageId] = openslide.open_slide(f'/vsis3/{BUCKET_NAME}/{imageId}.svs')
        properties = dict(osr.properties)
        return respond(json.dumps(properties), content_type='application/json')
    except openslide.OpenSlideError:
        return respond(f'Image ID {imageId} not found', None, 404)
    except Exception as e:
        return respond(None, e, 400)

def label_handler(event, context):
    """ Handler for image label requests.
        Returns: a base64-encoded label image """
    try:
        imageId = event['pathParameters']['imageId']
        logger.info(imageId)
        if imageId in open_slides:
            osr = open_slides[imageId]
        else:
            osr = open_slides[imageId] = openslide.open_slide(f'/vsis3/{BUCKET_NAME}/{imageId}.svs')
        image = osr.associated_images.get('label').convert('RGB')
        buf = BytesIO()
        image.save(buf, 'jpeg', quality=TILE_QUALITY)
        image.close()
        return respond(base64.b64encode(buf.getvalue()), content_type=f'image/jpeg')
    except openslide.OpenSlideError:
        return respond(f'Image ID {imageId} not found', None, 404)
    except Exception as e:
        return respond(None, e, 400)

def thumbnail_handler(event, context):
    """ Handler for image thumbnail requests. 
        Returns: a base64-encoded thumbnail image """
    try:
        imageId = event['pathParameters']['imageId']
        logger.info(imageId)
        if imageId in open_slides:
            osr = open_slides[imageId]
        else:
            osr = open_slides[imageId] = openslide.open_slide(f'/vsis3/{BUCKET_NAME}/{imageId}.svs')
        image = osr.associated_images.get('thumbnail').convert('RGB')
        buf = BytesIO()
        image.save(buf, 'jpeg', quality=TILE_QUALITY)
        image.close()
        return respond(base64.b64encode(buf.getvalue()), content_type=f'image/jpeg')
    except openslide.OpenSlideError:
        return respond(f'Image ID {imageId} not found', None, 404)
    except Exception as e:
        return respond(None, e, 400)

def tile_handler(event, context):
    """ Handler for IIIF protocol requests.
        Returns: an IIIF image tile """
    try:
        # image-service/{imageId}/x,y,w,h/720,/0/default.jpg
        logger.info(event['rawPath'])
        pathParameters = event['pathParameters']
        imageId = pathParameters['imageId']

        region = re.match(r'(?P<x>\d+),(?P<y>\d+),(?P<w>\d+),(?P<h>\d+)', pathParameters['region'])
        if not region:
            raise ValueError(f'Bad resource request: {pathParameters["region"]}')
        # match = re.match(r'\d*,\d*', pathParameters['size'])
        # if not match:
        #     raise ValueError(f'Bad resource request: {pathParameters["size"]]}')
        
        if imageId in open_slides:
            osr = open_slides[imageId]
        else:
            osr = open_slides[imageId] = openslide.open_slide(f'/vsis3/{BUCKET_NAME}/{imageId}.svs')
        colorTransform = get_color_transform(osr.properties.get(ICC_PROFILE_PROPERTY_NAME))

        x = int(region.group('x'))
        y = int(region.group('y'))
        w = int(region.group('w'))
        h = int(region.group('h'))
        downsample = max(w//TILE_SIZE, h//TILE_SIZE)
        downsamples = list(map(lambda d: round(d), osr.level_downsamples))
        level = get_best_level_for_downsample(osr, downsample)
        size = (TILE_SIZE,TILE_SIZE)
        region_size = tuple(l * downsample // downsamples[level] for l in size)
        tile_im = osr.read_region((x,y), level, region_size)
        if tile_im.size != size:
            tile_im.thumbnail(size, Image.ANTIALIAS)
        if colorTransform:
            tile_im = ImageCms.applyTransform(tile_im, colorTransform)
        tile_im = tile_im.convert('RGB')
        buf = BytesIO()
        tile_im.save(buf, 'jpeg', quality=TILE_QUALITY)
        tile_im.close()
        return respond(base64.b64encode(buf.getvalue()), content_type=f'image/jpeg')
    except openslide.OpenSlideError:
        return respond(f'Image ID {imageId} not found', None, 404)
    except Exception as e:
        return respond(None, e, 400)
