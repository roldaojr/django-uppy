# Uppy Compatible Views for Django Multipart Upload

This module provides Uppy Companion compatible views for both TUS protocol and S3 multipart uploads, enabling seamless integration with the Uppy JavaScript file uploader.

## Features

- **TUS Protocol Support**: Full implementation of TUS 1.0.0 protocol for resumable uploads
- **S3 Multipart Upload**: Direct-to-S3 multipart uploads with presigned URLs
- **Local Storage Support**: Fallback to local storage when S3 is not configured
- **Django Integration**: Built on Django REST Framework with proper permissions and error handling

## Endpoints

### TUS Protocol Endpoints

| Method | Path | Description |
|--------|------|-------------|
| OPTIONS | `/tus/` | Server capabilities and supported extensions |
| POST | `/tus/` | Create new upload |
| HEAD | `/tus/{upload_id}/` | Get upload status |
| PATCH | `/tus/{upload_id}/` | Upload chunk |
| DELETE | `/tus/{upload_id}/` | Terminate upload |

### S3 Multipart Upload Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/s3/multipart/` | Initiate multipart upload |
| POST | `/s3/multipart/` | Complete multipart upload |
| DELETE | `/s3/multipart/` | Abort multipart upload |
| PUT | `/s3/multipart/` | Upload part (local storage only) |

## Configuration

Add the URLs to your Django project:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    # ... other urls
    path('upload/', include('django_multipart_upload.urls')),
]
```

### Settings

Configure the multipart upload settings in your Django settings:

```python
# settings.py

# Maximum upload size for TUS protocol (default: 5GB)
MULTIPART_UPLOAD_TUS_MAX_SIZE = 5 * 1024 * 1024 * 1024

# Permission classes for the views
MULTIPART_UPLOAD_PERMISSION_CLASSES = [
    'rest_framework.permissions.IsAuthenticated',
]

# Temporary path for local uploads
MULTIPART_UPLOAD_TMP_PATH = 'tmp/uploads'

# Chunk size for multipart uploads
MULTIPART_UPLOAD_CHUNK_SIZE = 50 * 1024 * 1024  # 50MB
```

## Usage Examples

### TUS Protocol with Uppy

```javascript
import Uppy from '@uppy/core'
import Dashboard from '@uppy/dashboard'
import Tus from '@uppy/tus'

const uppy = new Uppy()
  .use(Dashboard, { inline: true, target: '#dashboard' })
  .use(Tus, {
    endpoint: '/upload/tus/',
    resume: true,
    autoRetry: true,
    retryDelays: [0, 1000, 3000, 5000],
  })
```

### S3 Multipart Upload with Uppy

```javascript
import Uppy from '@uppy/core'
import Dashboard from '@uppy/dashboard'
import AwsS3 from '@uppy/aws-s3'

const uppy = new Uppy()
  .use(Dashboard, { inline: true, target: '#dashboard' })
  .use(AwsS3, {
    endpoint: '/upload/s3/multipart/',
    getUploadParameters: (file) => {
      return fetch('/upload/s3/multipart/', {
        method: 'GET',
        headers: {
          accept: 'application/json',
          'content-type': 'application/json',
        },
        body: JSON.stringify({
          filename: file.name,
          type: file.type,
        }),
      })
      .then((response) => response.json())
    },
  })
```

## Storage Configuration

### S3 Storage

Configure S3 storage in your Django settings:

```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'your-region'

# Optional: Set custom ACL
AWS_DEFAULT_ACL = 'public-read'
```

### Local Storage

For local storage, the views will automatically detect and use Django's default file storage.

## S3 CORS Configuration

Add the following CORS configuration to your S3 bucket:

```json
[
  {
    "AllowedHeaders": [
      "content-type",
      "x-amz-content-sha256",
      "x-amz-date",
      "authorization"
    ],
    "AllowedMethods": ["GET", "POST", "PUT"],
    "AllowedOrigins": ["https://your-domain.com"],
    "ExposeHeaders": ["ETag", "Location"],
    "MaxAgeSeconds": 3000
  },
  {
    "AllowedHeaders": [],
    "AllowedMethods": ["GET"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": [],
    "MaxAgeSeconds": 3000
  }
]
```

## API Response Formats

### TUS Upload Creation

```http
POST /upload/tus/
HTTP/1.1 201 Created
Location: /upload/tus/550e8400-e29b-41d4-a716-446655440000/
Tus-Resumable: 1.0.0
Cache-Control: no-store
```

### S3 Multipart Initiation

```json
{
  "uploadId": "abc123",
  "key": "uploads/abc123/filename.jpg",
  "parts_urls": [
    "https://your-bucket.s3.amazonaws.com/uploads/abc123/filename.jpg?partNumber=1&uploadId=abc123&signature=...",
    "https://your-bucket.s3.amazonaws.com/uploads/abc123/filename.jpg?partNumber=2&uploadId=abc123&signature=..."
  ],
  "complete_url": "/upload/s3/multipart/?uploadId=abc123&filename=filename.jpg"
}
```

### S3 Multipart Completion

```json
{
  "location": "https://your-bucket.s3.amazonaws.com/uploads/abc123/filename.jpg",
  "etag": "\"d41d8cd98f00b204e9800998ecf8427e\"",
  "key": "uploads/abc123/filename.jpg"
}
```

## Error Handling

The views return appropriate HTTP status codes and error messages:

- `400 Bad Request`: Missing required parameters
- `404 Not Found`: Upload not found
- `409 Conflict`: Upload offset mismatch (TUS)
- `412 Precondition Failed`: Unsupported TUS version
- `413 Request Entity Too Large`: File exceeds maximum size
- `415 Unsupported Media Type`: Invalid content type (TUS)
- `500 Internal Server Error`: Server error

## Security Considerations

1. **Authentication**: Configure appropriate permission classes
2. **File Size Limits**: Set reasonable maximum upload sizes
3. **File Types**: Validate file types on the server side
4. **S3 Permissions**: Ensure proper S3 bucket permissions and CORS settings
5. **Rate Limiting**: Consider implementing rate limiting for upload endpoints

## Testing

Run the tests to ensure everything works correctly:

```bash
python manage.py test django_multipart_upload
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check your S3 bucket CORS configuration
2. **Permission Denied**: Verify your permission classes and authentication
3. **Upload Fails**: Check S3 credentials and bucket permissions
4. **Large Files**: Ensure your server can handle large file uploads (timeout, memory)

### Debug Mode

Enable debug mode to see detailed error messages:

```python
# settings.py
MULTIPART_UPLOAD_DEBUG = True
```

## License

This module is part of the django_multipart_upload package and follows the same license terms.
