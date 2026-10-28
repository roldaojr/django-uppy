import logging

from django.core.files.storage import Storage, storages
from django.http import HttpRequest
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ..settings import get_setting

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class BaseUploadView(View):
    def dispatch(
        self, request: HttpRequest, storage: str | None = None, *args, **kwargs
    ):
        self.storage_name = storage or "default"
        self.storage: Storage = storages[self.storage_name]
        return super().dispatch(request, *args, **kwargs)

    def get_upload_params(self, kwargs: dict):
        filename = kwargs.get("filename")
        content_type = kwargs.get("type")
        tmp_path = get_setting("TMP_PATH")
        upload_id = get_random_string(32)
        key = f"{tmp_path}/{upload_id}-{slugify(filename)}"
        return key, content_type
