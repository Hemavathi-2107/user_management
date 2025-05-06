from minio import Minio, S3Error
from settings.config import settings

"""
This module exposes a configured MinIO client.  Any bucket-existence checks
or creation are performed at runtime (either lazily or on startup), not at import.
"""

# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_USE_SSL
)

def ensure_bucket_exists(bucket_name: str) -> None:
    """
    Make sure the given bucket exists.  If the existence check or creation fails,
    log (or ignore) but don’t raise—so tests and imports won’t blow up.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
    except S3Error:
        # Could log a warning here; swallow so import/runtime isn’t killed
        pass

def upload_profile_picture(file_data: bytes, file_name: str) -> str:
    """
    Uploads a profile picture to MinIO.
    Args:
        file_data (bytes): File content to upload.
        file_name (str): Name of the file.
    Returns:
        str: URL to the uploaded file.
    Raises:
        ValueError: If the file type is unsupported.
        S3Error: If MinIO upload fails.
    """
    # Validate file type
    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
    ext = file_name.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported file type: .{ext}")

    # Ensure bucket exists (safe to call on every upload)
    ensure_bucket_exists(settings.MINIO_BUCKET_NAME)

    # Perform upload
    minio_client.put_object(
        settings.MINIO_BUCKET_NAME,
        file_name,
        file_data,
        length=-1,
        part_size=10 * 1024 * 1024
    )

    return f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{file_name}"

def get_profile_picture_url(file_name: str) -> str:
    """
    Generates a presigned URL for a profile picture.
    Args:
        file_name (str): Name of the file.
    Returns:
        str: Presigned URL for the file.
    Raises:
        S3Error: If MinIO presign fails.
    """
    return minio_client.get_presigned_url(
        "GET", settings.MINIO_BUCKET_NAME, file_name
    )