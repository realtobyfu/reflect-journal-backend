import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid
from typing import Optional
from app.config import get_settings

settings = get_settings()

class StorageService:
    def __init__(self):
        self.s3_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
    
    async def upload_file(self, file: UploadFile, folder: str) -> Optional[str]:
        if not self.s3_client:
            # For development, return a mock URL
            return f"https://placeholder.com/{folder}/{file.filename}"
        
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1]
            file_name = f"{folder}/{uuid.uuid4()}.{file_extension}"
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file.file,
                settings.s3_bucket_name,
                file_name,
                ExtraArgs={'ContentType': file.content_type}
            )
            
            # Return URL
            return f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_name}"
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return None

storage_service = StorageService() 