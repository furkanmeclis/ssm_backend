import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
from PIL import Image
import os
import io
import uuid

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_digitalocean_spaces(file, file_name):
    """
    Upload a file to DigitalOcean Spaces and return the file URL.
    """
    session = boto3.session.Session()
    client = session.client(
        's3',
        region_name=os.getenv('DO_SPACES_REGION'),
        endpoint_url=os.getenv('DO_SPACES_ENDPOINT_URL'),
        aws_access_key_id=os.getenv('DO_SPACES_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('DO_SPACES_SECRET_KEY'),
    )

    try:
        client.put_object(
            Bucket=os.getenv('DO_SPACES_NAME'),
            Key=f'{file_name}',
            Body=file,
            ACL='public-read',
            ContentType='image/jpeg'
        )
        return f"{os.getenv('DO_SPACES_CDN_ENDPOINT_URL')}/{file_name}"
    except NoCredentialsError:
        logger.error("Credentials not available")
    except ClientError as e:
        logger.error(f"Client error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    return None

def process_image_and_upload_to_digitalocean(image, folder_name, width, height):
    """
    Process the image to maintain aspect ratio, convert it to JPEG, and upload.
    """
    try:
        # Open the image using Pillow and convert it if not in RGB mode
        with Image.open(image) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((width, height))

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)

            file_name = f"{folder_name}/{uuid.uuid4().hex}.jpg"
            return upload_to_digitalocean_spaces(img_byte_arr, file_name)
    except Exception as e:
        logger.error(f"Error processing or uploading image: {str(e)}")
    return None
