"""S3-compatible storage client for file operations."""

import io
import os
from datetime import datetime, timedelta
from typing import AsyncIterator, BinaryIO, Optional

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageError(Exception):
    """Base exception for storage operations."""

    pass


class FileNotFoundError(StorageError):
    """File not found in storage."""

    pass


class UploadError(StorageError):
    """Error during file upload."""

    pass


class StorageClient:
    """Async S3-compatible storage client.

    Supports AWS S3, MinIO, DigitalOcean Spaces, and other S3-compatible services.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """Initialize storage client with configuration.

        Args:
            endpoint_url: S3 endpoint URL (None for AWS S3)
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            bucket_name: S3 bucket name
            region: AWS region
        """
        self.endpoint_url = endpoint_url or settings.s3_endpoint_url
        self.access_key_id = access_key_id or settings.s3_access_key_id
        self.secret_access_key = secret_access_key or settings.s3_secret_access_key
        self.bucket_name = bucket_name or settings.s3_bucket_name
        self.region = region or settings.s3_region

        self._session = aioboto3.Session()
        self._config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

    def _get_client_kwargs(self) -> dict:
        """Get keyword arguments for S3 client."""
        kwargs = {
            "service_name": "s3",
            "region_name": self.region,
            "config": self._config,
        }

        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url

        if self.access_key_id and self.secret_access_key:
            kwargs["aws_access_key_id"] = self.access_key_id
            kwargs["aws_secret_access_key"] = self.secret_access_key

        return kwargs

    async def upload_file(
        self,
        file_data: BinaryIO | bytes,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload a file to S3.

        Args:
            file_data: File content as bytes or file-like object
            key: S3 object key (path)
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the file

        Returns:
            The S3 object key

        Raises:
            UploadError: If upload fails
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            async with self._session.client(**self._get_client_kwargs()) as s3:
                if isinstance(file_data, bytes):
                    await s3.put_object(
                        Bucket=self.bucket_name,
                        Key=key,
                        Body=file_data,
                        **extra_args,
                    )
                else:
                    await s3.upload_fileobj(
                        file_data,
                        self.bucket_name,
                        key,
                        ExtraArgs=extra_args if extra_args else None,
                    )

            return key
        except ClientError as e:
            raise UploadError(f"Failed to upload file: {e}") from e

    async def upload_file_multipart(
        self,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Initiate a multipart upload.

        Args:
            key: S3 object key
            content_type: MIME type of the file
            metadata: Optional metadata

        Returns:
            Upload ID for the multipart upload
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            async with self._session.client(**self._get_client_kwargs()) as s3:
                response = await s3.create_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=key,
                    **extra_args,
                )
                return response["UploadId"]
        except ClientError as e:
            raise UploadError(f"Failed to initiate multipart upload: {e}") from e

    async def upload_part(
        self,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
    ) -> dict:
        """Upload a part of a multipart upload.

        Args:
            key: S3 object key
            upload_id: Multipart upload ID
            part_number: Part number (1-10000)
            body: Part data

        Returns:
            Dict with ETag and PartNumber
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                response = await s3.upload_part(
                    Bucket=self.bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=body,
                )
                return {
                    "ETag": response["ETag"],
                    "PartNumber": part_number,
                }
        except ClientError as e:
            raise UploadError(f"Failed to upload part {part_number}: {e}") from e

    async def complete_multipart_upload(
        self,
        key: str,
        upload_id: str,
        parts: list[dict],
    ) -> str:
        """Complete a multipart upload.

        Args:
            key: S3 object key
            upload_id: Multipart upload ID
            parts: List of uploaded parts with ETag and PartNumber

        Returns:
            The S3 object key
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.complete_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
                return key
        except ClientError as e:
            raise UploadError(f"Failed to complete multipart upload: {e}") from e

    async def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        """Abort a multipart upload and clean up uploaded parts.

        Args:
            key: S3 object key
            upload_id: Multipart upload ID
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.abort_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=key,
                    UploadId=upload_id,
                )
        except ClientError:
            # Ignore errors when aborting - upload may already be completed/aborted
            pass

    async def download_file(self, key: str) -> bytes:
        """Download a file from S3.

        Args:
            key: S3 object key

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                response = await s3.get_object(Bucket=self.bucket_name, Key=key)
                return await response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {key}") from e
            raise StorageError(f"Failed to download file: {e}") from e

    async def download_file_stream(self, key: str) -> AsyncIterator[bytes]:
        """Download a file from S3 as a stream.

        Args:
            key: S3 object key

        Yields:
            Chunks of file content
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                response = await s3.get_object(Bucket=self.bucket_name, Key=key)
                async for chunk in response["Body"].iter_chunks():
                    yield chunk
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {key}") from e
            raise StorageError(f"Failed to download file: {e}") from e

    async def delete_file(self, key: str) -> None:
        """Delete a file from S3.

        Args:
            key: S3 object key
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise StorageError(f"Failed to delete file: {e}") from e

    async def delete_files(self, keys: list[str]) -> None:
        """Delete multiple files from S3.

        Args:
            keys: List of S3 object keys
        """
        if not keys:
            return

        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                # S3 delete_objects accepts up to 1000 keys at a time
                for i in range(0, len(keys), 1000):
                    batch = keys[i : i + 1000]
                    await s3.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={"Objects": [{"Key": key} for key in batch]},
                    )
        except ClientError as e:
            raise StorageError(f"Failed to delete files: {e}") from e

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3.

        Args:
            key: S3 object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.head_object(Bucket=self.bucket_name, Key=key)
                return True
        except ClientError:
            return False

    async def get_file_info(self, key: str) -> dict:
        """Get file metadata from S3.

        Args:
            key: S3 object key

        Returns:
            Dict with file metadata (size, content_type, last_modified, etc.)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                response = await s3.head_object(Bucket=self.bucket_name, Key=key)
                return {
                    "size": response["ContentLength"],
                    "content_type": response.get("ContentType"),
                    "last_modified": response["LastModified"],
                    "etag": response["ETag"],
                    "metadata": response.get("Metadata", {}),
                }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File not found: {key}") from e
            raise StorageError(f"Failed to get file info: {e}") from e

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        """Generate a presigned URL for file access.

        Args:
            key: S3 object key
            expires_in: URL expiry time in seconds
            method: S3 method (get_object, put_object)

        Returns:
            Presigned URL
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                url = await s3.generate_presigned_url(
                    ClientMethod=method,
                    Params={"Bucket": self.bucket_name, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned URL: {e}") from e

    async def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict]:
        """List files in S3 bucket.

        Args:
            prefix: Key prefix to filter files
            max_keys: Maximum number of keys to return

        Returns:
            List of file info dicts
        """
        try:
            files = []
            async with self._session.client(**self._get_client_kwargs()) as s3:
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=max_keys,
                ):
                    for obj in page.get("Contents", []):
                        files.append(
                            {
                                "key": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"],
                                "etag": obj["ETag"],
                            }
                        )
            return files
        except ClientError as e:
            raise StorageError(f"Failed to list files: {e}") from e

    async def copy_file(self, source_key: str, dest_key: str) -> str:
        """Copy a file within the bucket.

        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key

        Returns:
            Destination key
        """
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                await s3.copy_object(
                    Bucket=self.bucket_name,
                    CopySource={"Bucket": self.bucket_name, "Key": source_key},
                    Key=dest_key,
                )
                return dest_key
        except ClientError as e:
            raise StorageError(f"Failed to copy file: {e}") from e

    async def ensure_bucket_exists(self) -> None:
        """Ensure the S3 bucket exists, create if not."""
        try:
            async with self._session.client(**self._get_client_kwargs()) as s3:
                try:
                    await s3.head_bucket(Bucket=self.bucket_name)
                except ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        await s3.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                "LocationConstraint": self.region
                            }
                            if self.region != "us-east-1"
                            else {},
                        )
        except ClientError as e:
            raise StorageError(f"Failed to ensure bucket exists: {e}") from e


# Global storage client instance
storage_client = StorageClient()


def get_storage_client() -> StorageClient:
    """Get the storage client instance.

    Returns:
        StorageClient instance
    """
    return storage_client
