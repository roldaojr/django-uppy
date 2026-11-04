import json

from botocore.stub import ANY
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .test_s3 import BUCKET_NAME, UPLOAD_ID, S3ViewTestCase

TUS_HEADERS = {"HTTP_TUS_RESUMABLE": "1.0.0"}

# REST framework settings (SessionAuthentication + IsAuthenticated) come from demo/test_settings.py
drf_urls = override_settings(ROOT_URLCONF="django_uppy.tests.drf_urls")


class LoginMixin:
    def login(self):
        user = get_user_model().objects.create_user("uploader", password="unused")
        self.client.force_login(user)


@drf_urls
class RestFrameworkTusTest(LoginMixin, TestCase):
    def setUp(self):
        self.url = reverse("uppy-tus-upload", args=["default"])

    def create_upload(self):
        return self.client.post(self.url, HTTP_UPLOAD_LENGTH="5", **TUS_HEADERS)

    def test_anonymous_is_denied(self):
        self.assertEqual(self.create_upload().status_code, 403)

    def test_authenticated_upload(self):
        self.login()
        response = self.create_upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Tus-Resumable"], "1.0.0")
        location = response["Location"]

        response = self.client.head(location, **TUS_HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Upload-Length"], "5")
        self.assertEqual(response["Upload-Offset"], "0")

        response = self.client.patch(
            location,
            b"hello",
            content_type="application/offset+octet-stream",
            HTTP_UPLOAD_OFFSET="0",
            **TUS_HEADERS,
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Upload-Offset"], "5")

        response = self.client.delete(location, **TUS_HEADERS)
        self.assertEqual(response.status_code, 204)


@drf_urls
class RestFrameworkS3Test(LoginMixin, S3ViewTestCase):
    def init_multipart(self):
        return self.client.post(
            reverse("uppy-s3-multipart-init", args=["bucket"]),
            json.dumps({"filename": "video.mp4", "type": "video/mp4"}),
            content_type="application/json",
        )

    def test_anonymous_is_denied(self):
        self.assertEqual(self.init_multipart().status_code, 403)

    def test_authenticated_multipart_init(self):
        self.stubber.add_response(
            "create_multipart_upload",
            {"Bucket": BUCKET_NAME, "Key": "key", "UploadId": UPLOAD_ID},
            {"Bucket": BUCKET_NAME, "Key": ANY, "ContentType": ANY},
        )
        self.login()

        response = self.init_multipart()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["uploadId"], UPLOAD_ID)
        self.assert_tmp_key(response.json()["key"], "videomp4")


@drf_urls
class RestFrameworkLocalUploadTest(LoginMixin, TestCase):
    def get_upload_url(self):
        url = reverse("uppy-s3-upload", args=["default"])
        return self.client.get(url, {"filename": "photo.jpg", "type": "image/jpeg"})

    def put(self, url: str):
        return self.client.put(url, b"content", content_type="application/octet-stream")

    def test_anonymous_cannot_get_upload_url(self):
        self.assertEqual(self.get_upload_url().status_code, 403)

    def test_signed_url_authorizes_upload(self):
        self.login()
        url = self.get_upload_url().json()["url"]
        self.client.logout()

        self.assertEqual(self.put(url).status_code, 200)

    def test_bad_signature_is_denied(self):
        self.login()
        url = self.get_upload_url().json()["url"]

        self.assertEqual(self.put(f"{url}tampered").status_code, 403)
