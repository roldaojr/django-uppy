import base64
import json
import time

from django.core.exceptions import BadRequest
from django.core.files.storage import storages, Storage
from django.http import HttpRequest, HttpResponse, Http404
from django.urls import reverse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from ..utils import get_file_upload_path
from ..settings import get_setting


@method_decorator(csrf_exempt, name="dispatch")
class TusUploadView(View):
    """
    TUS protocol implementation for resumable uploads.
    Compatible with Uppy Companion TUS plugin.
    """

    TUS_VERSION = "1.0.0"
    TUS_EXTENSIONS = "creation,expiration,termination"
    TUS_MAX_SIZE = get_setting("TUS_MAX_SIZE", 5 * 1024 * 1024 * 1024)  # 5GB default
    storage: Storage
    request: HttpRequest
    tmp_path: str

    def __init__(self):
        self.storage = storages[get_setting("STORAGE_NAME", "default")]
        self.tmp_path = get_setting("TMP_PATH", "z-uploads.tmp").strip("/")

    def _check_version(self):
        """Check TUS version"""
        tus_version = self.request.META.get("HTTP_TUS_RESUMABLE")
        if not tus_version or tus_version != self.TUS_VERSION:
            response = HttpResponse(status=412)
            response["Tus-Version"] = self.TUS_VERSION
            raise Http404(response)
        return None

    def _read_file_info(self, file_path: str):
        """Read file info from storage"""
        try:
            with self.storage.open(f"{file_path}.info", "r") as info_file:
                return json.loads(info_file.read())
        except FileNotFoundError:
            raise Http404("File info not found")

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in ["post", "put", "patch"]:
            version_mismatch = self._check_version()
            if version_mismatch is not None:
                return version_mismatch
        response = super().dispatch(request, *args, **kwargs)
        response["Tus-Resumable"] = self.TUS_VERSION
        response["Cache-Control"] = "no-store"
        return response

    def options(self, request, *args, **kwargs):
        """TUS protocol OPTIONS request - returns server capabilities"""
        response = HttpResponse(status=204)
        response["Tus-Version"] = self.TUS_VERSION
        response["Tus-Extension"] = self.TUS_EXTENSIONS
        response["Tus-Max-Size"] = str(self.TUS_MAX_SIZE)
        return response

    def post(self, request: HttpRequest):
        """TUS protocol POST request - create new upload"""
        upload_length = request.META.get("HTTP_UPLOAD_LENGTH")
        if not upload_length:
            raise BadRequest("Upload-Length header is required")
        try:
            upload_length = int(upload_length)
            if upload_length > self.TUS_MAX_SIZE:
                return HttpResponse(
                    status=413, content="Upload size exceeds maximum allowed"
                )
        except ValueError:
            raise BadRequest("Invalid Upload-Length header")
        # Get upload metadata
        upload_metadata = request.META.get("HTTP_UPLOAD_METADATA", "")
        metadata = {}
        if upload_metadata:
            for pair in upload_metadata.split(","):
                if " " in pair:
                    key, value = pair.split(" ", 1)
                    # Decode base64 encoded value
                    metadata[key] = base64.b64decode(value).decode("utf-8")
        # Generate unique upload ID
        upload_id = get_random_string(32)
        upload_path = f"{self.tmp_path}/{upload_id}"
        # Create empty file for upload
        with self.storage.open(upload_path, "wb"):
            pass  # Create empty file
        # Return upload URL
        response = HttpResponse(status=201)
        response["Location"] = self.request.build_absolute_uri(
            reverse("uppy-tus-upload", kwargs={"upload_id": upload_id})
        )
        return response

    def head(self, request, upload_id, *args, **kwargs):
        """TUS protocol HEAD request - get upload status"""
        file_path = f"{self.tmp_path}/{upload_id}"
        upload_info = self._read_file_info(file_path)
        current_offset = self.storage.size(file_path)
        response = HttpResponse(status=200)
        response["Upload-Offset"] = str(current_offset)
        response["Upload-Length"] = str(upload_info["size"])
        return response

    def patch(self, request: HttpRequest, upload_id, *args, **kwargs):
        """TUS protocol PATCH request - upload chunk"""
        # Check content type
        content_type = request.content_type
        if content_type != "application/offset+octet-stream":
            return HttpResponse(
                status=415,
                content="Content-Type must be application/offset+octet-stream",
            )

        # Get upload offset
        try:
            upload_offset = int(request.META.get("HTTP_UPLOAD_OFFSET"))
        except ValueError:
            raise BadRequest("Invalid Upload-Offset header")

        # Get upload offset
        file_path = f"{self.tmp_path}/{upload_id}"
        try:
            current_offset = self.storage.size(file_path)
        except FileNotFoundError:
            raise Http404("Upload not found")
        if upload_offset != current_offset:
            return HttpResponse(status=409, content="Upload offset mismatch")

        # Write chunk data
        chunk_data = request.body
        with self.storage.open(file_path, "wb+") as f:
            f.seek(upload_offset)
            f.write(chunk_data)

        new_offset = current_offset + len(chunk_data)

        response = HttpResponse(status=204)
        response["Upload-Offset"] = str(new_offset)
        return response

    def delete(self, request, upload_id, *args, **kwargs):
        """TUS protocol DELETE request - terminate upload"""
        self._check_version()
        file_path = f"{self.tmp_path}/{upload_id}"
        try:
            self.storage.delete(file_path)
        except FileNotFoundError:
            pass
        response = HttpResponse(status=204)
        return response
