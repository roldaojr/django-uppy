"""
Example Django views for handling Uppy file uploads.

This module demonstrates how to process Uppy uploads in Django views,
including handling both TUS and S3 multipart upload responses.
"""

import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _

from .uppy_forms import (
    SingleFileUploadForm,
    MultipleFileUploadForm,
    ImageUploadForm,
    DocumentUploadForm,
    ProfilePictureForm,
    GalleryUploadForm,
)


def upload_examples(request):
    """
    View showing all upload form examples.
    """
    if request.method == 'POST':
        # Handle different forms based on submit button
        form_type = request.POST.get('form_type')
        
        if form_type == 'single':
            form = SingleFileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                return handle_single_upload(request, form)
        
        elif form_type == 'multiple':
            form = MultipleFileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                return handle_multiple_upload(request, form)
        
        elif form_type == 'image':
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                return handle_image_upload(request, form)
        
        elif form_type == 'document':
            form = DocumentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                return handle_document_upload(request, form)
        
        elif form_type == 'profile':
            form = ProfilePictureForm(request.POST, request.FILES)
            if form.is_valid():
                return handle_profile_upload(request, form)
    
    # Initialize forms for GET request
    context = {
        'single_form': SingleFileUploadForm(),
        'multiple_form': MultipleFileUploadForm(),
        'image_form': ImageUploadForm(),
        'document_form': DocumentUploadForm(),
        'profile_form': ProfilePictureForm(),
    }
    
    return render(request, 'django_multipart_upload/upload_template.html', context)


def handle_single_upload(request, form):
    """Handle single file upload from Uppy."""
    cleaned_data = form.cleaned_data
    file_data = cleaned_data['file']
    
    # file_data structure from Uppy:
    # {
    #     "name": "filename.jpg",
    #     "size": 1234567,
    #     "type": "image/jpeg",
    #     "url": "https://example.com/uploads/filename.jpg",
    #     "uploadURL": "https://example.com/upload/tus/uuid/",
    #     "id": "uppy-file-id"
    # }
    
    # Process the file data
    title = cleaned_data['title']
    description = cleaned_data['description']
    
    # Here you would typically:
    # 1. Save file information to database
    # 2. Process the file if needed
    # 3. Create thumbnails for images
    # 4. Send notifications
    
    # Example database save:
    # UploadedFile.objects.create(
    #     title=title,
    #     description=description,
    #     filename=file_data['name'],
    #     file_url=file_data['url'],
    #     file_size=file_data['size'],
    #     mime_type=file_data['type'],
    #     upload_type='tus' if 'uploadURL' in file_data else 's3'
    # )
    
    messages.success(request, _('File "{}" uploaded successfully!').format(file_data['name']))
    return redirect('upload_examples')


def handle_multiple_upload(request, form):
    """Handle multiple file upload from Uppy."""
    cleaned_data = form.cleaned_data
    files_data = cleaned_data['files']
    
    collection_name = cleaned_data['name']
    
    # files_data can be a list of file objects or a single file
    if isinstance(files_data, dict):
        files = [files_data]
    else:
        files = files_data
    
    uploaded_files = []
    for file_data in files:
        # Process each file
        uploaded_files.append({
            'name': file_data['name'],
            'size': file_data['size'],
            'type': file_data['type'],
            'url': file_data['url'],
        })
        
        # Save to database
        # UploadedFile.objects.create(
        #     collection_name=collection_name,
        #     filename=file_data['name'],
        #     file_url=file_data['url'],
        #     file_size=file_data['size'],
        #     mime_type=file_data['type']
        # )
    
    messages.success(
        request, 
        _('Successfully uploaded {} files to collection "{}"!').format(
            len(uploaded_files), collection_name
        )
    )
    return redirect('upload_examples')


def handle_image_upload(request, form):
    """Handle image upload with validation."""
    cleaned_data = form.cleaned_data
    image_data = cleaned_data['image']
    
    caption = cleaned_data['caption']
    alt_text = cleaned_data['alt_text']
    
    # Process image
    # - Create thumbnails
    # - Extract EXIF data
    # - Validate image integrity
    # - Apply watermarks if needed
    
    # Example:
    # from PIL import Image
    # from io import BytesIO
    # import requests
    # 
    # # Download image from URL
    # response = requests.get(image_data['url'])
    # img = Image.open(BytesIO(response.content))
    # 
    # # Create thumbnail
    # img.thumbnail((200, 200))
    # thumbnail_url = save_thumbnail(img)
    
    messages.success(
        request, 
        _('Image "{}" uploaded successfully!').format(image_data['name'])
    )
    return redirect('upload_examples')


def handle_document_upload(request, form):
    """Handle document upload with type validation."""
    cleaned_data = form.cleaned_data
    document_data = cleaned_data['document']
    
    document_name = cleaned_data['document_name']
    category = cleaned_data['category']
    
    # Process document
    # - Extract text from PDF
    # - Validate document integrity
    # - Create preview images
    # - Index for search
    
    messages.success(
        request, 
        _('Document "{}" uploaded successfully!').format(document_data['name'])
    )
    return redirect('upload_examples')


def handle_profile_upload(request, form):
    """Handle profile picture upload."""
    cleaned_data = form.cleaned_data
    profile_data = cleaned_data['profile_picture']
    
    # Update user profile
    # - Crop profile picture
    # - Generate different sizes
    # - Update user model
    
    messages.success(request, _('Profile picture updated successfully!'))
    return redirect('upload_examples')


@require_http_methods(["POST"])
@csrf_exempt
def upload_progress(request):
    """
    AJAX endpoint to check upload progress.
    """
    upload_id = request.POST.get('upload_id')
    
    # In a real implementation, you would:
    # 1. Check upload status from database
    # 2. Return progress information
    # 3. Handle errors appropriately
    
    # Example response:
    progress_data = {
        'upload_id': upload_id,
        'status': 'uploading',
        'progress': 75,
        'bytes_uploaded': 750000,
        'total_bytes': 1000000,
        'speed': 250000,  # bytes per second
        'eta': 1.0,  # estimated time remaining in seconds
    }
    
    return JsonResponse(progress_data)


@require_http_methods(["POST"])
@csrf_exempt
def cancel_upload(request):
    """
    AJAX endpoint to cancel an ongoing upload.
    """
    upload_id = request.POST.get('upload_id')
    
    # Cancel upload logic:
    # 1. Abort TUS upload if using TUS
    # 2. Abort S3 multipart upload if using S3
    # 3. Clean up temporary files
    # 4. Update database status
    
    return JsonResponse({'status': 'cancelled', 'upload_id': upload_id})


@require_http_methods(["POST"])
@csrf_exempt
def retry_upload(request):
    """
    AJAX endpoint to retry a failed upload.
    """
    upload_id = request.POST.get('upload_id')
    
    # Retry upload logic:
    # 1. Check why upload failed
    # 2. Restart from last successful chunk
    # 3. Update upload status
    
    return JsonResponse({'status': 'retrying', 'upload_id': upload_id})


def upload_success(request):
    """
    Success page after upload completion.
    """
    return render(request, 'django_multipart_upload/upload_success.html')


def upload_list(request):
    """
    List all uploaded files for the current user.
    """
    # In a real implementation:
    # files = UploadedFile.objects.filter(user=request.user)
    # return render(request, 'django_multipart_upload/upload_list.html', {'files': files})
    
    return render(request, 'django_multipart_upload/upload_list.html', {'files': []})


# Example model for storing upload information
"""
from django.db import models
from django.contrib.auth.models import User

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    filename = models.CharField(max_length=255)
    file_url = models.URLField()
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    upload_type = models.CharField(max_length=10)  # 'tus' or 's3'
    upload_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.user.username})"


class FileCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"


class CollectionFile(models.Model):
    collection = models.ForeignKey(FileCollection, on_delete=models.CASCADE, related_name='files')
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['added_at']
"""
