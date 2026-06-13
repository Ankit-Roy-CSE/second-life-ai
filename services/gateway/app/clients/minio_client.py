"""
MinIO/S3 client for media uploads.

Gateway handles media upload when creating returns.
Uploads files to MinIO (S3-compatible) and stores object keys in Return.media[].
"""

import uuid
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from shared_py.web.errors import AppError

from app.config import settings


class MinIOClient:
    """
    S3-compatible client for MinIO media storage.
    
    Handles:
    - File uploads to the configured bucket
    - Generates S3 object keys with UUID prefixes
    - Ensures bucket exists
    """

    def __init__(self):
        """Initialize MinIO/S3 client."""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Ensure the bucket exists, create if it doesn't.
        
        Safe to call multiple times (idempotent).
        """
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                except ClientError as create_error:
                    # Log but don't fail — bucket might have been created by another service
                    print(f"Warning: Could not create bucket {self.bucket}: {create_error}")
            else:
                # Other error, log but don't fail
                print(f"Warning: Error checking bucket {self.bucket}: {e}")

    def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to MinIO and return the S3 object key.
        
        Args:
            file_obj: File-like object (bytes)
            filename: Original filename (for extension)
            content_type: MIME type (optional, defaults to octet-stream)
        
        Returns:
            S3 object key (e.g., "media/abc-123-def-456.jpg")
        
        Raises:
            AppError(502) if upload fails
        """
        # Generate unique object key
        file_extension = filename.split(".")[-1] if "." in filename else "bin"
        object_key = f"media/{uuid.uuid4()}.{file_extension}"

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_obj,
                ContentType=content_type,
            )
            return object_key
        except ClientError as e:
            raise AppError(
                status_code=502,
                code="media_upload_failed",
                message=f"Failed to upload media to storage: {e}",
            ) from e

    def upload_bytes(
        self,
        data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload raw bytes to MinIO.
        
        Convenience wrapper around upload_file for in-memory data.
        
        Args:
            data: Bytes to upload
            filename: Original filename (for extension)
            content_type: MIME type (optional)
        
        Returns:
            S3 object key
        """
        file_obj = BytesIO(data)
        return self.upload_file(file_obj, filename, content_type)

    def get_object_url(self, object_key: str) -> str:
        """
        Get the public URL for an object.
        
        For demo purposes, constructs the URL. In production, would use presigned URLs.
        
        Args:
            object_key: S3 object key (e.g., "media/abc-123.jpg")
        
        Returns:
            Full URL to the object
        """
        return f"{settings.s3_endpoint_url}/{self.bucket}/{object_key}"


# Singleton instance
minio_client = MinIOClient()
