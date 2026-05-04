import boto3
from botocore.exceptions import ClientError

from ..config import settings
from .base import BaseStorage


class S3Storage(BaseStorage):
    def __init__(self) -> None:
        kwargs: dict = {
            "aws_access_key_id": settings.s3_access_key,
            "aws_secret_access_key": settings.s3_secret_key,
            "region_name": settings.s3_region,
        }
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.s3_bucket

    def _key(self, content_hash: str) -> str:
        return f"{content_hash}.lz4"

    def write(self, content_hash: str, compressed_data: bytes) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=self._key(content_hash),
            Body=compressed_data,
        )

    def read(self, content_hash: str) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self._bucket, Key=self._key(content_hash)
            )
            return response["Body"].read()
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise FileNotFoundError(f"No S3 object for hash {content_hash}") from exc
            raise

    def delete(self, content_hash: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=self._key(content_hash))

    def exists(self, content_hash: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=self._key(content_hash))
            return True
        except ClientError:
            return False
