import json
import re
from urllib.parse import parse_qs, urlparse

from botocore.exceptions import ClientError
from botocore.stub import ANY, Stubber
from django.core.files.storage import storages
from django.test import TestCase
from django.urls import reverse

from django_uppy.settings import get_setting

STORAGE_NAME = "bucket"
BUCKET_NAME = "test-bucket"
UPLOAD_ID = "upload-123"


class S3ViewTestCase(TestCase):
    """Base test case with the boto client of the S3 storage stubbed"""

    def setUp(self):
        self.storage = storages[STORAGE_NAME]
        self.stubber = Stubber(self.storage.bucket.meta.client)
        self.stubber.activate()
        self.addCleanup(self.stubber.deactivate)

    def tearDown(self):
        self.stubber.assert_no_pending_responses()

    def assert_tmp_key(self, key: str, slug: str):
        tmp_path = re.escape(get_setting("TMP_PATH"))
        self.assertRegex(key, rf"^{tmp_path}/[A-Za-z0-9]{{32}}-{slug}$")

    def assert_presigned_url(self, url: str, key: str) -> dict:
        parsed = urlparse(url)
        self.assertIn(BUCKET_NAME, f"{parsed.netloc}{parsed.path}")
        self.assertTrue(parsed.path.endswith(key))
        query = parse_qs(parsed.query)
        self.assertIn("X-Amz-Signature", query)
        return query


class S3UploadViewTest(S3ViewTestCase):
    def test_get_presigned_put_url(self):
        url = reverse("uppy-s3-upload", args=[STORAGE_NAME])
        response = self.client.get(url, {"filename": "photo.jpg", "type": "image/jpeg"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["method"], "PUT")
        self.assertEqual(data["fields"], {})
        self.assertEqual(data["headers"], {})
        key = urlparse(data["url"]).path.split(f"{BUCKET_NAME}/")[-1].lstrip("/")
        self.assert_tmp_key(key, "photojpg")
        self.assert_presigned_url(data["url"], key)


class S3MultipartInitViewTest(S3ViewTestCase):
    def test_initiate_multipart_upload(self):
        self.stubber.add_response(
            "create_multipart_upload",
            {"Bucket": BUCKET_NAME, "Key": "key", "UploadId": UPLOAD_ID},
            {"Bucket": BUCKET_NAME, "Key": ANY, "ContentType": ANY},
        )
        url = reverse("uppy-s3-multipart-init", args=[STORAGE_NAME])
        response = self.client.post(
            url,
            json.dumps({"filename": "video.mp4", "type": "video/mp4"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["uploadId"], UPLOAD_ID)
        self.assert_tmp_key(data["key"], "videomp4")


class S3MultipartPartViewTest(S3ViewTestCase):
    def test_get_presigned_part_url(self):
        key = f"{get_setting('TMP_PATH')}/abc-videomp4"
        url = reverse(
            "uppy-s3-multipart-part", args=[STORAGE_NAME, UPLOAD_ID, 3]
        )
        response = self.client.get(url, {"key": key})

        self.assertEqual(response.status_code, 200)
        query = self.assert_presigned_url(response.json()["url"], key)
        self.assertEqual(query["partNumber"], ["3"])
        self.assertEqual(query["uploadId"], [UPLOAD_ID])


class S3MultipartCompleteViewTest(S3ViewTestCase):
    key = f"{get_setting('TMP_PATH')}/abc-videomp4"
    parts = [{"PartNumber": 1, "ETag": '"etag-1"'}, {"PartNumber": 2, "ETag": '"etag-2"'}]

    def complete(self, parts: list):
        url = reverse(
            "uppy-s3-multipart-complete", args=[STORAGE_NAME, UPLOAD_ID]
        )
        return self.client.post(
            f"{url}?key={self.key}",
            json.dumps({"parts": parts}),
            content_type="application/json",
        )

    def expected_params(self) -> dict:
        return {
            "Bucket": BUCKET_NAME,
            "Key": self.key,
            "UploadId": UPLOAD_ID,
            "MultipartUpload": {"Parts": self.parts},
        }

    def test_complete_multipart_upload(self):
        location = f"https://{BUCKET_NAME}.s3.amazonaws.com/{self.key}"
        self.stubber.add_response(
            "complete_multipart_upload",
            {"Location": location, "ETag": '"final-etag"'},
            self.expected_params(),
        )
        response = self.complete(self.parts)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"location": location, "etag": '"final-etag"', "key": self.key},
        )

    def test_complete_without_parts(self):
        response = self.complete([])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "parts are required"})

    def test_complete_client_error_propagates(self):
        self.stubber.add_client_error(
            "complete_multipart_upload",
            service_error_code="NoSuchUpload",
            http_status_code=404,
            expected_params=self.expected_params(),
        )
        with self.assertRaises(ClientError):
            self.complete(self.parts)
