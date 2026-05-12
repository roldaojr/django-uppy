import json
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.files.storage import default_storage
from rest_framework.test import APIClient
from rest_framework import status

from django_multipart_upload.uppy_views import TusUploadView, UppyS3MultipartView


class TusUploadViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.view = TusUploadView()
        
    def test_options_request(self):
        """Test TUS OPTIONS request returns server capabilities"""
        response = self.client.options('/upload/tus/')
        
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['Tus-Resumable'], '1.0.0')
        self.assertIn('Tus-Version', response)
        self.assertIn('Tus-Extension', response)
        self.assertIn('Tus-Max-Size', response)
        self.assertEqual(response['Cache-Control'], 'no-store')
    
    def test_post_create_upload(self):
        """Test TUS POST request creates new upload"""
        headers = {
            'HTTP_TUS_RESUMABLE': '1.0.0',
            'HTTP_UPLOAD_LENGTH': '1024',
            'HTTP_UPLOAD_METADATA': 'filename dGVzdC5qcGc=',  # base64 encoded 'test.jpg'
        }
        
        response = self.client.post('/upload/tus/', **headers)
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('Location', response)
        self.assertEqual(response['Tus-Resumable'], '1.0.0')
        
        # Verify upload info file was created
        location = response['Location']
        upload_id = location.split('/')[-2]
        info_path = f'z-uploads.tmp/{upload_id}.info'
        self.assertTrue(default_storage.exists(info_path))
    
    def test_post_invalid_version(self):
        """Test TUS POST with invalid version returns 412"""
        headers = {
            'HTTP_TUS_RESUMABLE': '0.1.0',
            'HTTP_UPLOAD_LENGTH': '1024',
        }
        
        response = self.client.post('/upload/tus/', **headers)
        
        self.assertEqual(response.status_code, 412)
        self.assertIn('Tus-Version', response)
    
    def test_post_missing_length(self):
        """Test TUS POST without Upload-Length returns 400"""
        headers = {
            'HTTP_TUS_RESUMABLE': '1.0.0',
        }
        
        response = self.client.post('/upload/tus/', **headers)
        
        self.assertEqual(response.status_code, 400)
    
    def test_head_upload_status(self):
        """Test TUS HEAD request returns upload status"""
        # First create an upload
        headers = {
            'HTTP_TUS_RESUMABLE': '1.0.0',
            'HTTP_UPLOAD_LENGTH': '1024',
        }
        create_response = self.client.post('/upload/tus/', **headers)
        
        # Then check status
        location = create_response['Location']
        headers = {'HTTP_TUS_RESUMABLE': '1.0.0'}
        response = self.client.head(location, **headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Upload-Offset', response)
        self.assertIn('Upload-Length', response)
        self.assertEqual(response['Tus-Resumable'], '1.0.0')
    
    def test_head_nonexistent_upload(self):
        """Test TUS HEAD for non-existent upload returns 404"""
        upload_id = uuid.uuid4()
        headers = {'HTTP_TUS_RESUMABLE': '1.0.0'}
        response = self.client.head(f'/upload/tus/{upload_id}/', **headers)
        
        self.assertEqual(response.status_code, 404)
    
    def test_patch_upload_chunk(self):
        """Test TUS PATCH request uploads chunk"""
        # Create upload first
        headers = {
            'HTTP_TUS_RESUMABLE': '1.0.0',
            'HTTP_UPLOAD_LENGTH': '1024',
        }
        create_response = self.client.post('/upload/tus/', **headers)
        location = create_response['Location']
        
        # Upload chunk
        chunk_data = b'test data'
        headers = {
            'HTTP_TUS_RESUMABLE': '1.0.0',
            'HTTP_UPLOAD_OFFSET': '0',
            'content_type': 'application/offset+octet-stream',
        }
        response = self.client.patch(location, chunk_data, **headers)
        
        self.assertEqual(response.status_code, 204)
        self.assertIn('Upload-Offset', response)
        self.assertEqual(response['Upload-Offset'], str(len(chunk_data)))
    
    def test_delete_upload(self):
        """Test TUS DELETE request terminates upload"""
        # Create upload first
        headers = {
            'HTTP_TUS_RESUMABLE': '1.0.0',
            'HTTP_UPLOAD_LENGTH': '1024',
        }
        create_response = self.client.post('/upload/tus/', **headers)
        location = create_response['Location']
        
        # Delete upload
        headers = {'HTTP_TUS_RESUMABLE': '1.0.0'}
        response = self.client.delete(location, **headers)
        
        self.assertEqual(response.status_code, 204)
        
        # Verify files are deleted
        upload_id = location.split('/')[-2]
        info_path = f'z-uploads.tmp/{upload_id}.info'
        self.assertFalse(default_storage.exists(info_path))


class UppyS3MultipartViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_get_initiate_local_multipart(self, mock_hasattr):
        """Test GET request initiates local multipart upload"""
        mock_hasattr.return_value = False  # Simulate local storage
        
        params = {
            'filename': 'test.jpg',
            'partCount': '3',
            'type': 'image/jpeg',
        }
        response = self.client.get('/upload/s3/multipart/', params)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('uploadId', data)
        self.assertIn('parts_urls', data)
        self.assertIn('complete_url', data)
        self.assertEqual(len(data['parts_urls']), 3)
    
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_get_missing_parameters(self, mock_hasattr):
        """Test GET request without required parameters returns error"""
        mock_hasattr.return_value = False
        
        response = self.client.get('/upload/s3/multipart/')
        self.assertEqual(response.status_code, 400)
        
        response = self.client.get('/upload/s3/multipart/', {'filename': 'test.jpg'})
        self.assertEqual(response.status_code, 400)
        
        response = self.client.get('/upload/s3/multipart/', {'partCount': '3'})
        self.assertEqual(response.status_code, 400)
    
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_get_invalid_part_count(self, mock_hasattr):
        """Test GET request with invalid part count returns error"""
        mock_hasattr.return_value = False
        
        params = {
            'filename': 'test.jpg',
            'partCount': 'invalid',
        }
        response = self.client.get('/upload/s3/multipart/', params)
        
        self.assertEqual(response.status_code, 400)
    
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_put_upload_part_local(self, mock_hasattr):
        """Test PUT request uploads part for local storage"""
        mock_hasattr.return_value = False  # Simulate local storage
        
        # First initiate upload
        params = {'filename': 'test.jpg', 'partCount': '2'}
        init_response = self.client.get('/upload/s3/multipart/', params)
        data = json.loads(init_response.content)
        upload_id = data['uploadId']
        
        # Upload part
        part_url = data['parts_urls'][0]
        part_data = b'test chunk data'
        response = self.client.put(part_url, part_data)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('etag', response_data)
    
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_post_complete_local_multipart(self, mock_hasattr):
        """Test POST request completes local multipart upload"""
        mock_hasattr.return_value = False  # Simulate local storage
        
        # First initiate upload
        params = {'filename': 'test.jpg', 'partCount': '2'}
        init_response = self.client.get('/upload/s3/multipart/', params)
        data = json.loads(init_response.content)
        upload_id = data['uploadId']
        
        # Upload parts
        for i, part_url in enumerate(data['parts_urls'], 1):
            part_data = f'part {i}'.encode()
            self.client.put(part_url, part_data)
        
        # Complete upload
        complete_data = {
            'parts': [
                {'PartNumber': 1, 'ETag': 'etag1'},
                {'PartNumber': 2, 'ETag': 'etag2'},
            ]
        }
        response = self.client.post(data['complete_url'], complete_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('location', response_data)
        self.assertIn('key', response_data)
    
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_delete_abort_local_multipart(self, mock_hasattr):
        """Test DELETE request aborts local multipart upload"""
        mock_hasattr.return_value = False  # Simulate local storage
        
        # First initiate upload
        params = {'filename': 'test.jpg', 'partCount': '2'}
        init_response = self.client.get('/upload/s3/multipart/', params)
        data = json.loads(init_response.content)
        upload_id = data['uploadId']
        
        # Abort upload
        abort_url = f'/upload/s3/multipart/?uploadId={upload_id}&filename=test.jpg'
        response = self.client.delete(abort_url)
        
        self.assertEqual(response.status_code, 204)
    
    @patch('django_multipart_upload.uppy_views.hasattr')
    def test_s3_not_supported_direct_upload(self, mock_hasattr):
        """Test direct part upload not supported for S3"""
        mock_hasattr.return_value = True  # Simulate S3 storage
        
        params = {'uploadId': 'test123', 'partNumber': '1', 'filename': 'test.jpg'}
        response = self.client.put('/upload/s3/multipart/', **params)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('Direct part upload not supported for S3', data['error'])
