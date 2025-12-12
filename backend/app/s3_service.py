import os
import boto3
from botocore.config import Config
import logging

logger = logging.getLogger(__name__)

def get_s3_client():
    config = Config(signature_version='s3v4')
    return boto3.client(
        's3',
        endpoint_url=os.getenv('S3_ENDPOINT'),
        aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
        region_name='ru-central1',
        config=config
    )

def upload_to_s3(file_path: str, object_name: str):
    try:
        s3 = get_s3_client()
        bucket = os.getenv('S3_BUCKET')
        
        with open(file_path, 'rb') as f:
            s3.put_object(Bucket=bucket, Key=object_name, Body=f)
        
        url = f"https://{bucket}.storage.yandexcloud.net/{object_name}"
        logger.info(f"S3 OK: {url}")
        return url
    except Exception as e:
        logger.error(f"S3 fail: {e}")
        return file_path
