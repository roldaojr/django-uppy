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

# Upload behavior tests run without access control, see test_access_control.py
UPPY_LOGIN_REQUIRED = False

# Used by the REST framework views (django_uppy.rest_framework)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
