import hashlib
import json
from urllib.parse import urlencode
from django.core.files.base import ContentFile
from django.http.request import BadRequest
from django.urls import reverse
from django.views.generic import View
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.core.files.storage import storages, Storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from ..settings import get_setting
from ..utils import get_file_upload_path
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class BaseUploadView(View):
    def dispatch(self, request: HttpRequest, storage: str = None, *args, **kwargs):
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


class UploadView(BaseUploadView):
    def get(self, request: HttpRequest):
        """Get URL for single part upload"""
        upload_id = get_random_string(32)
        url = request.build_absolute_uri(
            reverse(
                "uppy-file-upload",
                kwargs={"storage": self.storage_name, "filename": upload_id},
            )
        )
        return JsonResponse({"method": "PUT", "url": url})


class MultipartInitView(BaseUploadView):
    def post(self, request: HttpRequest):
        """Initialize multipart upload"""
        data: dict = json.loads(request.body)
        filename = data.get("filename")
        upload_id = get_random_string(32)
        return JsonResponse({"uploadId": upload_id, "key": filename})


class MultipartPartView(BaseUploadView):
    def get(self, request: HttpRequest, upload_id: str, part_number: int):
        """Get URL for a part of a multipart upload"""
        key = request.GET.get("key")
        if not key:
            return JsonResponse({"error": "Missing key parameter"}, status=400)
        filename = f"{upload_id}/part{part_number}"
        url = request.build_absolute_uri(
            reverse(
                "uppy-file-upload",
                kwargs={"storage": self.storage_name, "filename": filename},
            )
        )
        return JsonResponse(dict(url=url + "?etag"))


class MultipartCompleteView(BaseUploadView):
    def post(self, request: HttpRequest, upload_id: str):
        """Complete a multipart upload"""
        key = request.GET.get("key")
        data: dict = json.loads(request.body)
        parts = data.get("parts", [])
        if not all([key, parts]):
            return JsonResponse({"error": "key and parts are required"}, status=400)
        try:
            final_path = get_file_upload_path(upload_id, filename=key)
            with self.storage.open(final_path, "wb+") as final_file:
                for part_num in range(1, len(parts) + 1):
                    part_path = get_file_upload_path(upload_id, part=part_num)
                    if self.storage.exists(part_path):
                        with self.storage.open(part_path, "rb") as part_file:
                            final_file.write(part_file.read())
                        self.storage.delete(part_path)
                    else:
                        raise BadRequest(f"Part {part_num} not found")
            # Clean up
            self.storage.delete(get_file_upload_path(upload_id))
            return JsonResponse(
                {
                    "location": self.storage.url(final_path),
                    "key": final_path,
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class UploadFileView(View):
    def put(self, request: HttpRequest, storage: str = None, filename: str = None):
        """Handle file upload to storage"""
        file_path = get_file_upload_path(filename)
        storage: Storage = storages[storage or "default"]
        storage.save(file_path, ContentFile(request.body))
        etag = hashlib.md5(request.body).hexdigest()
        return HttpResponse(headers={"Etag": etag})
