from django.core.files.storage import InvalidStorageError, Storage, storages
from django.http import Http404, HttpRequest

from .local import LocalHandler
from .result import UploadResult
from .s3 import S3Handler
from .tus import TusHandler

__all__ = [
    "LocalHandler",
    "S3Handler",
    "TusHandler",
    "UploadResult",
    "get_local_handler",
    "get_multipart_handler",
    "get_storage",
    "get_tus_handler",
]


def get_storage(name: str) -> Storage:
    try:
        return storages[name]
    except InvalidStorageError:
        raise Http404(f"Storage {name!r} not found")


def get_multipart_handler(storage_name: str, request: HttpRequest):
    """S3 handler for storages with a bucket, local handler otherwise"""
    storage = get_storage(storage_name)
    handler_class = S3Handler if hasattr(storage, "bucket") else LocalHandler
    return handler_class(storage, storage_name, request)


def get_local_handler(storage_name: str, request: HttpRequest) -> LocalHandler:
    return LocalHandler(get_storage(storage_name), storage_name, request)


def get_tus_handler(storage_name: str, request: HttpRequest) -> TusHandler:
    return TusHandler(get_storage(storage_name), storage_name, request)
