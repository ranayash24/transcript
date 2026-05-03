"""
Storage service using MinIO (self-hosted, free, S3-compatible).
MinIO runs as a Docker container — no account or payment needed.
"""
import io
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from ..config import get_settings


def _get_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",  # MinIO ignores this but boto3 requires it
    )


def ensure_bucket() -> None:
    """Create the bucket if it doesn't exist (called at startup)."""
    settings = get_settings()
    client = _get_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket_name)
    except ClientError:
        client.create_bucket(Bucket=settings.minio_bucket_name)


def upload_file(local_path: str, object_key: str, content_type: str = "application/octet-stream") -> str:
    settings = get_settings()
    client = _get_client()
    client.upload_file(
        local_path,
        settings.minio_bucket_name,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )
    return object_key


def upload_fileobj(file_obj, object_key: str, content_type: str = "application/octet-stream") -> str:
    settings = get_settings()
    client = _get_client()
    client.upload_fileobj(
        file_obj,
        settings.minio_bucket_name,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )
    return object_key


def download_file(object_key: str, local_path: str) -> None:
    settings = get_settings()
    client = _get_client()
    client.download_file(settings.minio_bucket_name, object_key, local_path)


def get_signed_url(object_key: str, expiry_hours: int | None = None) -> str:
    settings = get_settings()
    expiry = expiry_hours or settings.signed_url_expiry_hours
    client = _get_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket_name, "Key": object_key},
        ExpiresIn=expiry * 3600,
    )
    return url


def delete_object(object_key: str) -> None:
    settings = get_settings()
    client = _get_client()
    client.delete_object(Bucket=settings.minio_bucket_name, Key=object_key)
