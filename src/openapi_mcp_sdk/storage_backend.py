import os
from pathlib import Path


def _storage_backend() -> str:
    return os.getenv("MCP_STORAGE_BACKEND", "local").strip().lower()


def _storage_bucket() -> str:
    bucket = os.getenv("MCP_STORAGE_BUCKET", "").strip()
    if not bucket:
        raise RuntimeError("MCP_STORAGE_BUCKET is required for cloud storage backends")
    return bucket


def _storage_path() -> Path:
    return Path(os.getenv("MCP_STORAGE_PATH", "./openapi_storage")).expanduser()


def save_file(file_path: str, content: bytes, content_type: str) -> None:
    backend = _storage_backend()

    if backend == "local":
        target = _storage_path() / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return

    if backend == "gcs":
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("google-cloud-storage is required for MCP_STORAGE_BACKEND=gcs") from exc

        client = storage.Client()
        bucket = client.bucket(_storage_bucket())
        blob = bucket.blob(file_path)
        blob.upload_from_string(content, content_type=content_type)
        return

    if backend == "s3":
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for MCP_STORAGE_BACKEND=s3") from exc

        client = boto3.client(
            "s3",
            region_name=os.getenv("MCP_STORAGE_REGION") or None,
        )
        client.put_object(
            Bucket=_storage_bucket(),
            Key=file_path,
            Body=content,
            ContentType=content_type,
        )
        return

    raise RuntimeError(f"Unsupported MCP_STORAGE_BACKEND: {backend}")


def read_file(file_path: str) -> tuple[bytes, str]:
    backend = _storage_backend()

    if backend == "local":
        target = _storage_path() / file_path
        if not target.exists():
            raise FileNotFoundError(file_path)
        return target.read_bytes(), "application/octet-stream"

    if backend == "gcs":
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("google-cloud-storage is required for MCP_STORAGE_BACKEND=gcs") from exc

        client = storage.Client()
        bucket = client.bucket(_storage_bucket())
        blob = bucket.blob(file_path)
        if not blob.exists():
            raise FileNotFoundError(file_path)
        return blob.download_as_bytes(), blob.content_type or "application/octet-stream"

    if backend == "s3":
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as exc:
            raise RuntimeError("boto3 is required for MCP_STORAGE_BACKEND=s3") from exc

        client = boto3.client(
            "s3",
            region_name=os.getenv("MCP_STORAGE_REGION") or None,
        )
        try:
            obj = client.get_object(Bucket=_storage_bucket(), Key=file_path)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"NoSuchKey", "404"}:
                raise FileNotFoundError(file_path) from exc
            raise
        return obj["Body"].read(), obj.get("ContentType") or "application/octet-stream"

    raise RuntimeError(f"Unsupported MCP_STORAGE_BACKEND: {backend}")
