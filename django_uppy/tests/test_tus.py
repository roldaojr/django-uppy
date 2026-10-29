import uuid

from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse

from django_uppy.utils import get_file_upload_path

STORAGE_NAME = "default"


def upload_id_from_location(location: str) -> str:
    return location.rstrip("/").rsplit("/", 1)[-1]


class TusUploadViewTest(TestCase):
    def setUp(self):
        self.base_url = reverse("uppy-tus-upload", args=[STORAGE_NAME])

    def test_options_request(self):
        """Test TUS OPTIONS request returns server capabilities"""
        response = self.client.options(self.base_url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Tus-Resumable"], "1.0.0")
        self.assertIn("Tus-Version", response)
        self.assertIn("Tus-Extension", response)
        self.assertIn("Tus-Max-Size", response)
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_post_create_upload(self):
        """Test TUS POST request creates new upload"""
        headers = {
            "HTTP_TUS_RESUMABLE": "1.0.0",
            "HTTP_UPLOAD_LENGTH": "1024",
            "HTTP_UPLOAD_METADATA": "filename dGVzdC5qcGc=",  # base64 encoded 'test.jpg'
        }

        response = self.client.post(self.base_url, **headers)

        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        self.assertEqual(response["Tus-Resumable"], "1.0.0")

        # Verify upload info file was created
        location = response["Location"]
        upload_path = get_file_upload_path(upload_id_from_location(location))
        info_path = f"{upload_path}.info"
        self.assertTrue(default_storage.exists(info_path))

    def test_post_invalid_version(self):
        """Test TUS POST with invalid version returns 412"""
        headers = {
            "HTTP_TUS_RESUMABLE": "0.1.0",
            "HTTP_UPLOAD_LENGTH": "1024",
        }

        response = self.client.post(self.base_url, **headers)

        self.assertEqual(response.status_code, 412)
        self.assertIn("Tus-Version", response)

    def test_post_missing_length(self):
        """Test TUS POST without Upload-Length returns 400"""
        headers = {
            "HTTP_TUS_RESUMABLE": "1.0.0",
        }

        response = self.client.post(self.base_url, **headers)

        self.assertEqual(response.status_code, 400)

    def test_head_upload_status(self):
        """Test TUS HEAD request returns upload status"""
        # First create an upload
        headers = {
            "HTTP_TUS_RESUMABLE": "1.0.0",
            "HTTP_UPLOAD_LENGTH": "1024",
        }
        create_response = self.client.post(self.base_url, **headers)

        # Then check status
        location = create_response["Location"]
        headers = {"HTTP_TUS_RESUMABLE": "1.0.0"}
        response = self.client.head(location, **headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Upload-Offset", response)
        self.assertIn("Upload-Length", response)
        self.assertEqual(response["Tus-Resumable"], "1.0.0")

    def test_head_nonexistent_upload(self):
        """Test TUS HEAD for non-existent upload returns 404"""
        upload_id = uuid.uuid4()
        headers = {"HTTP_TUS_RESUMABLE": "1.0.0"}
        url = reverse("uppy-tus-upload", args=[STORAGE_NAME, upload_id])
        response = self.client.head(url, **headers)

        self.assertEqual(response.status_code, 404)

    def test_patch_upload_chunk(self):
        """Test TUS PATCH request uploads chunk"""
        # Create upload first
        headers = {
            "HTTP_TUS_RESUMABLE": "1.0.0",
            "HTTP_UPLOAD_LENGTH": "1024",
        }
        create_response = self.client.post(self.base_url, **headers)
        location = create_response["Location"]

        # Upload chunk
        chunk_data = b"test data"
        headers = {
            "HTTP_TUS_RESUMABLE": "1.0.0",
            "HTTP_UPLOAD_OFFSET": "0",
            "content_type": "application/offset+octet-stream",
        }
        response = self.client.patch(location, chunk_data, **headers)

        self.assertEqual(response.status_code, 204)
        self.assertIn("Upload-Offset", response)
        self.assertEqual(response["Upload-Offset"], str(len(chunk_data)))

    def test_delete_upload(self):
        """Test TUS DELETE request terminates upload"""
        # Create upload first
        headers = {
            "HTTP_TUS_RESUMABLE": "1.0.0",
            "HTTP_UPLOAD_LENGTH": "1024",
        }
        create_response = self.client.post(self.base_url, **headers)
        location = create_response["Location"]

        # Delete upload
        headers = {"HTTP_TUS_RESUMABLE": "1.0.0"}
        response = self.client.delete(location, **headers)

        self.assertEqual(response.status_code, 204)

        # Verify files are deleted
        upload_path = get_file_upload_path(upload_id_from_location(location))
        info_path = f"{upload_path}.info"
        self.assertFalse(default_storage.exists(upload_path))
        self.assertFalse(default_storage.exists(info_path))
