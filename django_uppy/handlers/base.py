from django.core.files.storage import Storage
from django.http import HttpRequest
from django.utils.crypto import get_random_string

from ..utils import get_file_upload_path


class BaseHandler:
    def __init__(self, storage: Storage, storage_name: str, request: HttpRequest):
        self.storage = storage
        self.storage_name = storage_name
        self.request = request

    def new_upload_key(self, filename: str) -> str:
        return get_file_upload_path(get_random_string(32), filename=filename)
