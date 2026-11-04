import hashlib
from urllib.parse import urlencode

from django.core.exceptions import BadRequest
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils.crypto import get_random_string

from ..utils import get_file_upload_path, sign_upload, verify_upload_signature
from .base import BaseHandler
from .result import UploadResult


class LocalHandler(BaseHandler):
    """S3 compatible uploads to any Django storage, through signed upload URLs"""

    def _upload_url(self, filename: str) -> str:
        url = reverse(
            "uppy-file-upload",
            kwargs={"storage": self.storage_name, "filename": filename},
        )
        query = urlencode({"signature": sign_upload(self.storage_name, filename)})
        return self.request.build_absolute_uri(f"{url}?{query}")

    def upload_params(self, filename: str, content_type: str) -> UploadResult:
        url = self._upload_url(get_random_string(32))
        return UploadResult(data={"method": "PUT", "url": url})

    def init_multipart(self, filename: str, content_type: str) -> UploadResult:
        return UploadResult(data={"uploadId": get_random_string(32), "key": filename})

    def part_url(self, upload_id: str, part_number: int, key: str) -> UploadResult:
        url = self._upload_url(f"{upload_id}/part{part_number}")
        return UploadResult(data={"url": f"{url}&etag"})

    def complete(self, upload_id: str, key: str, parts: list) -> UploadResult:
        final_path = get_file_upload_path(upload_id, filename=key)
        with self.storage.open(final_path, "wb+") as final_file:
            for part_num in range(1, len(parts) + 1):
                part_path = get_file_upload_path(upload_id, part=part_num)
                if not self.storage.exists(part_path):
                    raise BadRequest(f"Part {part_num} not found")
                with self.storage.open(part_path, "rb") as part_file:
                    final_file.write(part_file.read())
                self.storage.delete(part_path)
        # Clean up
        self.storage.delete(get_file_upload_path(upload_id))
        return UploadResult(
            data={"location": self.storage.url(final_path), "key": final_path}
        )

    def save_file(self, filename: str, signature: str | None, body: bytes):
        verify_upload_signature(self.storage_name, filename, signature)
        self.storage.save(get_file_upload_path(filename), ContentFile(body))
        etag = hashlib.md5(body, usedforsecurity=False).hexdigest()
        return UploadResult(headers={"Etag": etag})
