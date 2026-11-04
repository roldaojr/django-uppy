import base64
import json
from contextlib import suppress
from io import BytesIO

from django.core.exceptions import BadRequest
from django.core.files.base import ContentFile
from django.http import Http404
from django.urls import reverse
from django.utils.crypto import get_random_string

from ..settings import get_setting
from ..utils import get_file_upload_path
from .base import BaseHandler
from .result import UploadResult


class TusHandler(BaseHandler):
    """
    TUS protocol implementation for resumable uploads.
    Compatible with Uppy Companion TUS plugin.
    """

    TUS_VERSION = "1.0.0"
    TUS_EXTENSIONS = "creation,expiration,termination"
    RESPONSE_HEADERS = {"Tus-Resumable": TUS_VERSION, "Cache-Control": "no-store"}

    @property
    def max_size(self) -> int:
        return get_setting("TUS_MAX_SIZE")

    def _read_file_info(self, file_path: str) -> dict:
        """Read file info from storage"""
        try:
            with self.storage.open(f"{file_path}.info", "r") as info_file:
                return json.loads(info_file.read())
        except FileNotFoundError:
            raise Http404("File info not found")

    def _parse_metadata(self, upload_metadata: str) -> dict:
        metadata = {}
        for pair in upload_metadata.split(","):
            if " " in pair:
                key, value = pair.split(" ", 1)
                # Decode base64 encoded value
                metadata[key] = base64.b64decode(value).decode("utf-8")
        return metadata

    def check_version(self, tus_version: str | None) -> UploadResult | None:
        """Check TUS version, returns an error result on mismatch"""
        if tus_version != self.TUS_VERSION:
            return UploadResult(status=412, headers={"Tus-Version": self.TUS_VERSION})
        return None

    def options(self) -> UploadResult:
        """Server capabilities"""
        return UploadResult(
            status=204,
            headers={
                "Tus-Version": self.TUS_VERSION,
                "Tus-Extension": self.TUS_EXTENSIONS,
                "Tus-Max-Size": str(self.max_size),
            },
        )

    def create(self, upload_length: str | None, upload_metadata: str) -> UploadResult:
        """Create new upload"""
        if not upload_length:
            raise BadRequest("Upload-Length header is required")
        try:
            size = int(upload_length)
        except ValueError:
            raise BadRequest("Invalid Upload-Length header")
        if size > self.max_size:
            return UploadResult(
                status=413, content="Upload size exceeds maximum allowed"
            )
        upload_id = get_random_string(32)
        upload_path = get_file_upload_path(upload_id)
        # Create empty file for upload
        self.storage.save(upload_path, BytesIO())
        # Save upload info, read back by HEAD to resume uploads
        upload_info = {"size": size, "metadata": self._parse_metadata(upload_metadata)}
        self.storage.save(f"{upload_path}.info", ContentFile(json.dumps(upload_info)))
        location = self.request.build_absolute_uri(
            reverse(
                "uppy-tus-upload",
                kwargs={"storage": self.storage_name, "upload_id": upload_id},
            )
        )
        return UploadResult(status=201, headers={"Location": location})

    def status(self, upload_id: str) -> UploadResult:
        """Upload status"""
        file_path = get_file_upload_path(upload_id)
        upload_info = self._read_file_info(file_path)
        return UploadResult(
            headers={
                "Upload-Offset": str(self.storage.size(file_path)),
                "Upload-Length": str(upload_info["size"]),
            }
        )

    def write_chunk(
        self, upload_id: str, offset: str | None, content_type: str, body: bytes
    ) -> UploadResult:
        """Write an upload chunk"""
        if content_type != "application/offset+octet-stream":
            return UploadResult(
                status=415,
                content="Content-Type must be application/offset+octet-stream",
            )
        try:
            upload_offset = int(offset)
        except (TypeError, ValueError):
            raise BadRequest("Invalid Upload-Offset header")
        file_path = get_file_upload_path(upload_id)
        try:
            current_offset = self.storage.size(file_path)
        except FileNotFoundError:
            raise Http404("Upload not found")
        if upload_offset != current_offset:
            return UploadResult(status=409, content="Upload offset mismatch")
        with self.storage.open(file_path, "wb+") as f:
            f.seek(upload_offset)
            f.write(body)
        return UploadResult(
            status=204, headers={"Upload-Offset": str(current_offset + len(body))}
        )

    def terminate(self, upload_id: str) -> UploadResult:
        """Delete upload and its info file"""
        file_path = get_file_upload_path(upload_id)
        for path in (file_path, f"{file_path}.info"):
            with suppress(FileNotFoundError):
                self.storage.delete(path)
        return UploadResult(status=204)
