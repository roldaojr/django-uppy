import hashlib
import json
from urllib.parse import parse_qs, urlparse

from django.core.files.storage import storages
from django.test import TestCase, override_settings
from django.urls import reverse

from django_uppy.utils import get_file_upload_path

STORAGE_NAME = "default"


def upload_filename(url: str) -> str:
    """File name signed in an upload URL"""
    path = urlparse(url).path
    return path.split("/upload/", 1)[1]


class LocalUploadTestCase(TestCase):
    """Uploads to a storage without S3 support, through signed URLs"""

    def setUp(self):
        self.storage = storages[STORAGE_NAME]

    def get_upload_url(self) -> str:
        url = reverse("uppy-s3-upload", args=[STORAGE_NAME])
        response = self.client.get(url, {"filename": "photo.jpg", "type": "image/jpeg"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["method"], "PUT")
        return response.json()["url"]

    def put(self, url: str, content: bytes):
        return self.client.put(url, content, content_type="application/octet-stream")


class LocalSingleUploadTest(LocalUploadTestCase):
    def test_upload_to_signed_url(self):
        url = self.get_upload_url()
        self.assertIn("signature", parse_qs(urlparse(url).query))

        response = self.put(url, b"content")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Etag"], hashlib.md5(b"content").hexdigest())
        file_path = get_file_upload_path(upload_filename(url))
        with self.storage.open(file_path, "rb") as f:
            self.assertEqual(f.read(), b"content")

    def test_upload_without_signature(self):
        url = self.get_upload_url().split("?")[0]

        self.assertEqual(self.put(url, b"content").status_code, 403)

    def test_upload_with_signature_of_another_file(self):
        url = self.get_upload_url()
        other_url = self.get_upload_url()
        tampered = f"{url.split('?')[0]}?{urlparse(other_url).query}"

        self.assertEqual(self.put(tampered, b"content").status_code, 403)

    @override_settings(UPPY_UPLOAD_URL_MAX_AGE=-1)
    def test_upload_with_expired_signature(self):
        url = self.get_upload_url()

        self.assertEqual(self.put(url, b"content").status_code, 403)


class LocalMultipartUploadTest(LocalUploadTestCase):
    def test_multipart_upload(self):
        response = self.client.post(
            reverse("uppy-s3-multipart-init", args=[STORAGE_NAME]),
            json.dumps({"filename": "doc.pdf", "type": "application/pdf"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        upload_id, key = response.json()["uploadId"], response.json()["key"]

        chunks = [b"first-", b"second"]
        parts = []
        for part_number, chunk in enumerate(chunks, start=1):
            response = self.client.get(
                reverse(
                    "uppy-s3-multipart-part",
                    args=[STORAGE_NAME, upload_id, part_number],
                ),
                {"key": key},
            )
            self.assertEqual(response.status_code, 200)
            put_response = self.put(response.json()["url"], chunk)
            self.assertEqual(put_response.status_code, 200)
            parts.append({"PartNumber": part_number, "ETag": put_response["Etag"]})

        complete_url = reverse(
            "uppy-s3-multipart-complete", args=[STORAGE_NAME, upload_id]
        )
        response = self.client.post(
            f"{complete_url}?key={key}",
            json.dumps({"parts": parts}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        final_path = get_file_upload_path(upload_id, filename=key)
        self.assertEqual(response.json()["key"], final_path)
        with self.storage.open(final_path, "rb") as f:
            self.assertEqual(f.read(), b"".join(chunks))

    def test_part_url_without_key(self):
        url = reverse("uppy-s3-multipart-part", args=[STORAGE_NAME, "abc", 1])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "key is required"})
