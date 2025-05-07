import importlib
import io
import pytest

import settings.config as config
import app.utils.minio_client as mc  # <— the module, not the instance

class DummyClient:
    def __init__(self):
        self.buckets = set()
        self.uploads = []
        self.presigned_calls = []

    def bucket_exists(self, name):
        return name in self.buckets

    def make_bucket(self, name):
        self.buckets.add(name)

    def put_object(self, bucket, obj_name, data, length, part_size):
        if hasattr(data, "read"):
            content = data.read()
        else:
            content = data
        self.uploads.append((bucket, obj_name, content, length, part_size))

    def get_presigned_url(self, method, bucket, obj_name):
        url = f"https://dummy-minio/{bucket}/{obj_name}?method={method}"
        self.presigned_calls.append((method, bucket, obj_name))
        return url

@pytest.fixture(autouse=True)
def patch_minio_client(monkeypatch):
    # Create dummy and patch the module-level name
    dummy = DummyClient()
    monkeypatch.setattr(mc, "minio_client", dummy)

    # Patch settings so URLs point to our dummy endpoint
    monkeypatch.setattr(config.settings, "MINIO_ENDPOINT", "https://dummy-minio")
    monkeypatch.setattr(config.settings, "MINIO_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(config.settings, "MINIO_USE_SSL", True)

    yield dummy

def test_upload_profile_picture_success_bytes(patch_minio_client):
    data = b"PNGDATA"
    filename = "avatar.png"

    url = mc.upload_profile_picture(data, filename)

    assert url == "https://dummy-minio/test-bucket/avatar.png"
    assert patch_minio_client.uploads == [
        ("test-bucket", "avatar.png", data, -1, 10 * 1024 * 1024)
    ]

def test_upload_profile_picture_success_fileobj(patch_minio_client):
    data_stream = io.BytesIO(b"JPEGDATA")
    filename = "pic.jpeg"

    url = mc.upload_profile_picture(data_stream, filename)

    assert url.endswith("/test-bucket/pic.jpeg")
    assert patch_minio_client.uploads[0][2] == b"JPEGDATA"

@pytest.mark.parametrize("bad_ext", ["txt", "pdf", "exe"])
def test_upload_profile_picture_unsupported_extension(bad_ext, patch_minio_client):
    with pytest.raises(ValueError):
        mc.upload_profile_picture(b"DATA", f"file.{bad_ext}")
    assert patch_minio_client.uploads == []

def test_get_profile_picture_url(patch_minio_client):
    filename = "profile.gif"
    url = mc.get_profile_picture_url(filename)

    assert url == "https://dummy-minio/test-bucket/profile.gif?method=GET"
    assert patch_minio_client.presigned_calls == [("GET", "test-bucket", "profile.gif")]
