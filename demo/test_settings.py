from .settings import *
from .settings import STORAGES

STORAGES = {
    **STORAGES,
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "bucket": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": "test-bucket",
            "access_key": "testing",
            "secret_key": "testing",
            "region_name": "us-east-1",
            "signature_version": "s3v4",
        },
    },
}
