# Uppy Django Widget Documentation

This guide covers how to use the Uppy Django widget for seamless file upload integration in Django applications.

## Overview

The Uppy Django widget provides a modern, resumable file upload experience with support for:
- **TUS Protocol**: Resumable uploads that can be paused and resumed
- **S3 Multipart**: Direct-to-S3 uploads for better performance
- **Multiple Files**: Upload multiple files simultaneously
- **Drag & Drop**: Intuitive drag and drop interface
- **Progress Tracking**: Real-time upload progress
- **File Validation**: Client and server-side validation

## Quick Start

### 1. Install Dependencies

```bash
pip install django-multipart-upload
```

### 2. Configure URLs

Add to your Django `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    # ... other urls
    path('upload/', include('django_multipart_upload.urls')),
]
```

### 3. Basic Usage in Forms

```python
from django import forms
from django_multipart_upload.uppy_fields import UppyTusField

class UploadForm(forms.Form):
    title = forms.CharField(max_length=200)
    file = UppyTusField(
        label=_('Upload File'),
        widget_kwargs={
            'upload_type': 'tus',
            'max_files': 1,
            'height': 300,
        }
    )
```

### 4. Template Usage

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
{{ form.media.css }}
{% endblock %}

{% block content %}
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    
    {{ form.title.label_tag }}
    {{ form.title }}
    
    {{ form.file.label_tag }}
    {{ form.file }}
    
    <button type="submit">Upload</button>
</form>
{% endblock %}

{% block extra_js %}
{{ form.media.js }}
{% endblock %}
```

## Widget Types

### UppyWidget (Base Widget)

The base widget with full configuration options:

```python
from django_multipart_upload.uppy_widget import UppyWidget

file = UppyTusField(
    widget=UppyWidget(
        upload_type='tus',        # 'tus' or 's3'
        target='#uppy-dashboard', # Dashboard target
        auto_proceed=False,       # Auto-start upload
        allow_multiple=True,      # Allow multiple files
        max_files=5,             # Maximum files
        max_file_size=100*1024*1024,  # 100MB max
        allowed_file_types=['jpg', 'png'],  # Allowed extensions
        inline=False,            # Inline dashboard
        height=300,              # Dashboard height
        theme='light'            # Theme: 'light', 'dark', 'minimal'
    )
)
```

### UppyDashboardWidget

Optimized for dashboard display:

```python
from django_multipart_upload.uppy_widget import UppyDashboardWidget

file = UppyTusField(
    widget=UppyDashboardWidget(
        upload_type='s3',
        height=350,
        theme='dark'
    )
)
```

### UppyInlineWidget

Compact inline widget:

```python
from django_multipart_upload.uppy_widget import UppyInlineWidget

file = UppyTusField(
    widget=UppyInlineWidget(
        upload_type='tus',
        height=200,
        auto_proceed=True
    )
)
```

## Field Types

### UppyFileField

General-purpose file field:

```python
from django_multipart_upload.uppy_fields import UppyFileField

class MyForm(forms.Form):
    file = UppyFileField(
        upload_type='tus',
        max_files=5,
        max_file_size=50*1024*1024,  # 50MB
        allowed_file_types=['pdf', 'doc', 'docx']
    )
```

### UppyMultipleFileField

For multiple file uploads:

```python
from django_multipart_upload.uppy_fields import UppyMultipleFileField

class GalleryForm(forms.Form):
    images = UppyMultipleFileField(
        upload_type='s3',
        max_files=20,
        max_file_size=10*1024*1024  # 10MB per image
    )
```

### UppyImageField

Specialized for images:

```python
from django_multipart_upload.uppy_fields import UppyImageField

class ProfileForm(forms.Form):
    avatar = UppyImageField(
        upload_type='tus',
        max_files=1,
        max_file_size=5*1024*1024  # 5MB
    )
```

### UppyDocumentField

For document uploads:

```python
from django_multipart_upload.uppy_fields import UppyDocumentField

class DocumentForm(forms.Form):
    document = UppyDocumentField(
        upload_type='s3',
        max_files=1,
        max_file_size=100*1024*1024  # 100MB
    )
```

## Upload Protocols

### TUS Protocol

TUS provides resumable uploads that can be paused and resumed:

```python
file = UppyTusField(
    widget_kwargs={
        'upload_type': 'tus',
        'auto_proceed': False,  # Manual upload start
    }
)
```

**Benefits:**
- Resumable uploads
- Works well with unstable connections
- Server-side progress tracking

### S3 Multipart

Direct-to-S3 uploads for better performance:

```python
file = UppyS3Field(
    widget_kwargs={
        'upload_type': 's3',
        'auto_proceed': True,  # Auto-start upload
    }
)
```

**Benefits:**
- Better performance for large files
- Reduced server load
- Direct cloud storage

## Configuration

### Django Settings

```python
# settings.py

# TUS maximum upload size (default: 5GB)
MULTIPART_UPLOAD_TUS_MAX_SIZE = 5 * 1024 * 1024 * 1024

# Permission classes for upload views
MULTIPART_UPLOAD_PERMISSION_CLASSES = [
    'rest_framework.permissions.IsAuthenticated',
]

# Temporary storage path
MULTIPART_UPLOAD_TMP_PATH = 'tmp/uploads'

# Chunk size for uploads
MULTIPART_UPLOAD_CHUNK_SIZE = 50 * 1024 * 1024  # 50MB
```

### S3 Configuration

```python
# settings.py

# Use S3 storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# S3 credentials
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'us-east-1'

# Optional: Default ACL
AWS_DEFAULT_ACL = 'public-read'
```

### S3 CORS Configuration

Add this to your S3 bucket CORS configuration:

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

## Processing Uploads

### View Example

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from django_multipart_upload.uppy_fields import UppyTusField

class UploadForm(forms.Form):
    title = forms.CharField(max_length=200)
    file = UppyTusField(upload_type='tus')

def upload_view(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Get uploaded file data
            file_data = form.cleaned_data['file']
            
            # file_data structure:
            # {
            #     "name": "filename.jpg",
            #     "size": 1234567,
            #     "type": "image/jpeg",
            #     "url": "https://example.com/uploads/filename.jpg",
            #     "uploadURL": "https://example.com/upload/tus/uuid/",
            #     "id": "uppy-file-id"
            # }
            
            # Save to database
            # UploadedFile.objects.create(
            #     title=form.cleaned_data['title'],
            #     filename=file_data['name'],
            #     file_url=file_data['url'],
            #     file_size=file_data['size'],
            #     mime_type=file_data['type']
            # )
            
            messages.success(request, 'File uploaded successfully!')
            return redirect('upload_success')
    else:
        form = UploadForm()
    
    return render(request, 'upload.html', {'form': form})
```

### Model Integration

```python
from django.db import models
from django_multipart_upload.uppy_fields import UppyModelField

class Document(models.Model):
    title = models.CharField(max_length=200)
    file = UppyModelField(upload_to='documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
```

## Advanced Usage

### Custom Validation

```python
from django.core.exceptions import ValidationError
from django_multipart_upload.uppy_fields import UppyFileField

class ValidatedFileField(UppyFileField):
    def validate(self, value):
        super().validate(value)
        
        # Custom validation logic
        if isinstance(value, dict):
            filename = value['name']
            
            # Check filename pattern
            if not filename.startswith('doc_'):
                raise ValidationError('Filename must start with "doc_"')
            
            # Check file size
            if value['size'] > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('File too large')
```

### Custom Widget Themes

```python
from django_multipart_upload.uppy_widget import UppyWidget

class CustomUppyWidget(UppyWidget):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        # Add custom configuration
        context['custom_config'] = {
            'showLinkButton': False,
            'note': 'Custom upload note',
            'proudlyDisplayPoweredByUppy': False,
        }
        
        return context
```

### JavaScript Customization

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Access Uppy instance
    const uppy = window.UppyWidgets['your_widget_id'];
    
    if (uppy) {
        // Add custom event listeners
        uppy.on('file-added', (file) => {
            console.log('File added:', file.name);
        });
        
        uppy.on('upload-progress', (progress) => {
            console.log('Progress:', progress.percentage);
        });
        
        // Add custom plugins
        uppy.use(Uppy.Webcam, {
            target: '.uppy-webcam-container'
        });
    }
});
</script>
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check S3 bucket CORS configuration
   - Ensure allowed origins include your domain

2. **Upload Fails**
   - Verify S3 credentials and permissions
   - Check network connectivity
   - Review server logs for errors

3. **Large Files Timeout**
   - Increase server timeout settings
   - Use S3 multipart for better performance
   - Implement chunked uploads

4. **Widget Not Displaying**
   - Include `{{ form.media }}` in template
   - Check for JavaScript errors in browser console
   - Verify static files are served correctly

### Debug Mode

Enable debug mode for detailed logging:

```python
# settings.py
MULTIPART_UPLOAD_DEBUG = True
```

### Browser Console

Check browser console for:
- JavaScript errors
- Network request failures
- Uppy plugin initialization issues

## Performance Tips

1. **Use S3 for Large Files**
   - Direct uploads reduce server load
   - Better scalability

2. **Optimize Chunk Size**
   - Larger chunks for stable connections
   - Smaller chunks for unstable connections

3. **Implement Caching**
   - Cache upload progress
   - Store file metadata efficiently

4. **Monitor Storage**
   - Clean up failed uploads
   - Implement retention policies

## Security Considerations

1. **File Type Validation**
   - Validate on both client and server
   - Use MIME type checking
   - Scan uploaded files for malware

2. **Size Limits**
   - Set reasonable maximum file sizes
   - Monitor storage usage

3. **Access Control**
   - Configure proper permissions
   - Use authentication for uploads
   - Implement rate limiting

4. **Storage Security**
   - Use secure S3 bucket policies
   - Enable server-side encryption
   - Regular security audits

## Examples Repository

For complete working examples, see the `examples/` directory:

- `uppy_forms.py` - Form examples
- `uppy_views.py` - View examples
- `upload_template.html` - Template example

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review browser console for errors
3. Enable debug mode for detailed logging
4. Check Django and Uppy documentation

## License

This widget is part of the django-multipart-upload package and follows the same license terms.
