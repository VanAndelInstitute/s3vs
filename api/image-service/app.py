''' Lambda function code for image-service implementation. '''
import os
import base64
import json
from urllib.parse import urljoin
import re
from io import BytesIO
import logging
import openslide
from PIL import Image
from PIL import ImageCms
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
if os.environ.get('DEBUG', False):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

open_slides = {}
color_transforms = {
    'AT2': None,
    'ScanScope v1': None
}

def get_best_level_for_downsample(osr, downsample):
    ''' Use our own implementation of this since OpenSlide's doesn't handle
        the slightly-off Aperio SVS values.'''
    for i in range(osr.level_count):
        if round(downsample) < round(osr.level_downsamples[i]):
            return 0 if i == 0 else i-1
    return osr.level_count - 1

def get_color_transform(icc_profile_name):
    ''' Build the appropriate color transform, or
        retrieve it if already built. '''
    dest_icc = ImageCms.ImageCmsProfile(ICC_DEST)
    if not color_transforms[icc_profile_name]:
        if icc_profile_name == 'AT2':
            source_icc = ImageCms.ImageCmsProfile(ICC_AT2)
        elif icc_profile_name == 'ScanScope v1':
            source_icc = ImageCms.ImageCmsProfile(ICC_SCANSCOPE)
        else:
            return None
        intent = ImageCms.getDefaultIntent(source_icc)
        color_transforms[icc_profile_name] = ImageCms.buildTransform(
            source_icc, dest_icc, 'RGBA', 'RGBA', intent)
    return color_transforms[icc_profile_name]

def respond(msg, status=200, content_type=None):
    ''' Format the response message. '''
    response = {
        'statusCode': status,
        'body': msg,
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

    log_msg = { key: value if not isinstance(value, bytes) else value.decode('ascii')
                for key, value in response.items() }
    logger.debug(json.dumps(log_msg))

    return response

def info_handler(event, _context):
    ''' Handler for IIIF image information requests.
        Returns: an IIIF info.json response '''
    image_id = event['pathParameters']['imageId']
    logger.info(image_id)
    match = re.fullmatch(r'\w+', event['pathParameters']['imageId'])
    if not match:
        return respond('Invalid image ID', 404)
    if image_id in open_slides:
        osr = open_slides[image_id]
    else:
        try:
            osr = open_slides[image_id] = openslide.open_slide(
                f'/vsis3/{BUCKET_NAME}/{image_id}.svs')
        except openslide.OpenSlideError:
            logger.exception('Exception opening /vsis3/{%s}/{%s}.svs', BUCKET_NAME, image_id)
            return respond(f"Unsupported or missing image file with ID '{image_id}'", 404)
    width, height = osr.dimensions
    downsamples = list(map(round, osr.level_downsamples))
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

def properties_handler(event, _context):
    ''' Handler for image properties requests.
        Returns: OpenSlide properties '''
    image_id = event['pathParameters']['imageId']
    logger.info(image_id)
    if image_id in open_slides:
        osr = open_slides[image_id]
    else:
        try:
            osr = open_slides[image_id] = openslide.open_slide(
                f'/vsis3/{BUCKET_NAME}/{image_id}.svs')
        except openslide.OpenSlideError:
            logger.exception('Exception opening /vsis3/{%s}/{%s}.svs', BUCKET_NAME, image_id)
            return respond(f"Unsupported or missing image file with ID '{image_id}'", 404)
    properties = dict(osr.properties)
    return respond(json.dumps(properties), content_type='application/json')

def label_handler(event, _context):
    ''' Handler for image label requests.
        Returns: a base64-encoded label image '''
    image_id = event['pathParameters']['imageId']
    logger.info(image_id)
    if image_id in open_slides:
        osr = open_slides[image_id]
    else:
        try:
            osr = open_slides[image_id] = openslide.open_slide(
                f'/vsis3/{BUCKET_NAME}/{image_id}.svs')
        except openslide.OpenSlideError:
            logger.exception('Exception opening /vsis3/{%s}/{%s}.svs', BUCKET_NAME, image_id)
            return respond(f"Unsupported or missing image file with ID '{image_id}'", 404)
    image = osr.associated_images.get('label').convert('RGB')
    buf = BytesIO()
    image.save(buf, 'jpeg', quality=TILE_QUALITY)
    image.close()
    return respond(base64.b64encode(buf.getvalue()), content_type='image/jpeg')

def thumbnail_handler(event, _context):
    ''' Handler for image thumbnail requests.
        Returns: a base64-encoded thumbnail image '''
    image_id = event['pathParameters']['imageId']
    logger.info(image_id)
    if image_id in open_slides:
        osr = open_slides[image_id]
    else:
        try:
            osr = open_slides[image_id] = openslide.open_slide(
                f'/vsis3/{BUCKET_NAME}/{image_id}.svs')
        except openslide.OpenSlideError:
            logger.exception('Exception opening /vsis3/{%s}/{%s}.svs', BUCKET_NAME, image_id)
            return respond(f"Unsupported or missing image file with ID '{image_id}'", 404)
    image = osr.associated_images.get('thumbnail').convert('RGB')
    buf = BytesIO()
    image.save(buf, 'jpeg', quality=TILE_QUALITY)
    image.close()
    return respond(base64.b64encode(buf.getvalue()), content_type='image/jpeg')

def tile_handler(event, _context):
    ''' Handler for IIIF protocol requests.
        Returns: an IIIF image tile '''
    # image-service/{imageId}/x,y,w,h/720,/0/default.jpg
    logger.info(event['rawPath'])
    path_parameters = event['pathParameters']
    image_id = path_parameters['imageId']

    region = re.fullmatch(r'(?P<x>\d+),(?P<y>\d+),(?P<w>\d+),(?P<h>\d+)',
        path_parameters['region'])
    if not region:
        return respond(f'Bad resource request: {path_parameters["region"]}', 404)
    # match = re.fullmatch(r'\d*,\d*', path_parameters['size'])
    # if not match:
    #     return respond(f'Bad resource request: {path_parameters["size"]]}', 404)

    if image_id in open_slides:
        osr = open_slides[image_id]
    else:
        try:
            osr = open_slides[image_id] = openslide.open_slide(
                f'/vsis3/{BUCKET_NAME}/{image_id}.svs')
        except openslide.OpenSlideError:
            logger.exception('Exception opening /vsis3/{%s}/{%s}.svs', BUCKET_NAME, image_id)
            return respond(f"Unsupported or missing image file with ID '{image_id}'", 404)


    downsample = max(int(region.group('w'))//TILE_SIZE, int(region.group('h'))//TILE_SIZE)
    downsamples = list(map(round, osr.level_downsamples))
    level = get_best_level_for_downsample(osr, downsample)
    size = (TILE_SIZE,TILE_SIZE)
    region_size = tuple(l * downsample // downsamples[level] for l in size)
    try:
        tile_im = osr.read_region(
            (int(region.group('x')), int(region.group('y'))), level, region_size)
    except openslide.OpenSlideError:
        logger.exception('Exception reading /vsis3/{%s}/{%s}.svs', BUCKET_NAME, image_id)
        return respond(f"Error reading image file with ID '{image_id}'", 404)

    if tile_im.size != size:
        tile_im.thumbnail(size, Image.ANTIALIAS)
    color_transform = get_color_transform(osr.properties.get(ICC_PROFILE_PROPERTY_NAME))
    if color_transform:
        tile_im = ImageCms.applyTransform(tile_im, color_transform)
    tile_im = tile_im.convert('RGB')
    buf = BytesIO()
    tile_im.save(buf, 'jpeg', quality=TILE_QUALITY)
    tile_im.close()
    return respond(base64.b64encode(buf.getvalue()), content_type='image/jpeg')
