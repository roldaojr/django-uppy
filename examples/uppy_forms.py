"""
Example Django forms using Uppy widgets for file uploads.

This module demonstrates how to use the Uppy widget in various scenarios:
- Single file upload with TUS protocol
- Multiple file upload with S3 multipart
- Image upload with preview
- Document upload with validation
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from django_multipart_upload.uppy_fields import (
    UppyTusField,
    UppyS3Field,
    UppyMultipleFileField,
    UppyImageField,
    UppyDocumentField,
    UppyTusImageField,
    UppyS3ImageField,
)
from django_multipart_upload.uppy_widget import (
    UppyWidget,
    UppyDashboardWidget,
    UppyDragDropWidget,
    UppyInlineWidget,
)


class SingleFileUploadForm(forms.Form):
    """
    Example form for single file upload using TUS protocol.
    """
    title = forms.CharField(
        max_length=200,
        label=_('Title'),
        help_text=_('Enter a title for your file')
    )
    
    description = forms.CharField(
        widget=forms.Textarea,
        label=_('Description'),
        required=False,
        help_text=_('Optional description of the file')
    )
    
    file = UppyTusField(
        label=_('File'),
        help_text=_('Select a file to upload'),
        widget_kwargs={
            'upload_type': 'tus',
            'auto_proceed': False,
            'allow_multiple': False,
            'max_files': 1,
            'height': 250,
            'theme': 'light',
        }
    )


class MultipleFileUploadForm(forms.Form):
    """
    Example form for multiple file upload using S3 multipart.
    """
    name = forms.CharField(
        max_length=100,
        label=_('Collection Name'),
        help_text=_('Name for this collection of files')
    )
    
    files = UppyMultipleFileField(
        label=_('Files'),
        help_text=_('Upload multiple files (max 10)'),
        widget_kwargs={
            'upload_type': 's3',
            'auto_proceed': True,
            'allow_multiple': True,
            'max_files': 10,
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'height': 400,
            'theme': 'dark',
        }
    )


class ImageUploadForm(forms.Form):
    """
    Example form for image upload with validation and preview.
    """
    caption = forms.CharField(
        max_length=200,
        label=_('Caption'),
        help_text=_('Enter a caption for the image')
    )
    
    alt_text = forms.CharField(
        max_length=500,
        label=_('Alt Text'),
        required=False,
        help_text=_('Descriptive text for accessibility')
    )
    
    image = UppyTusImageField(
        label=_('Image'),
        help_text=_('Upload an image (JPG, PNG, GIF, WebP)'),
        widget_kwargs={
            'upload_type': 'tus',
            'auto_proceed': True,
            'allow_multiple': False,
            'max_files': 1,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'height': 300,
            'theme': 'light',
        }
    )


class DocumentUploadForm(forms.Form):
    """
    Example form for document upload with type validation.
    """
    document_name = forms.CharField(
        max_length=200,
        label=_('Document Name'),
        help_text=_('Name for the document')
    )
    
    category = forms.ChoiceField(
        choices=[
            ('contract', _('Contract')),
            ('invoice', _('Invoice')),
            ('report', _('Report')),
            ('other', _('Other')),
        ],
        label=_('Category'),
        help_text=_('Select document category')
    )
    
    document = UppyDocumentField(
        label=_('Document'),
        help_text=_('Upload a document (PDF, DOC, XLS, etc.)'),
        widget_kwargs={
            'upload_type': 's3',
            'auto_proceed': False,
            'allow_multiple': False,
            'max_files': 1,
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'height': 280,
        }
    )


class ProfilePictureForm(forms.Form):
    """
    Example form for profile picture upload with inline widget.
    """
    first_name = forms.CharField(
        max_length=50,
        label=_('First Name')
    )
    
    last_name = forms.CharField(
        max_length=50,
        label=_('Last Name')
    )
    
    bio = forms.CharField(
        widget=forms.Textarea,
        label=_('Bio'),
        required=False,
        max_length=500
    )
    
    profile_picture = UppyS3ImageField(
        label=_('Profile Picture'),
        help_text=_('Upload a profile picture'),
        widget_kwargs={
            'upload_type': 's3',
            'auto_proceed': True,
            'allow_multiple': False,
            'max_files': 1,
            'max_file_size': 5 * 1024 * 1024,  # 5MB
            'height': 200,
            'theme': 'minimal',
            'inline': True,
        }
    )


class GalleryUploadForm(forms.Form):
    """
    Example form for gallery image upload with multiple files.
    """
    gallery_name = forms.CharField(
        max_length=100,
        label=_('Gallery Name'),
        help_text=_('Name for this photo gallery')
    )
    
    description = forms.CharField(
        widget=forms.Textarea,
        label=_('Description'),
        required=False,
        help_text=_('Describe this gallery')
    )
    
    is_public = forms.BooleanField(
        label=_('Public Gallery'),
        required=False,
        help_text=_('Make this gallery publicly visible')
    )
    
    images = UppyImageField(
        label=_('Images'),
        help_text=_('Upload multiple images for the gallery'),
        widget_kwargs={
            'upload_type': 's3',
            'auto_proceed': True,
            'allow_multiple': True,
            'max_files': 20,
            'max_file_size': 15 * 1024 * 1024,  # 15MB per image
            'height': 350,
            'theme': 'dark',
        }
    )


class FileReplaceForm(forms.Form):
    """
    Example form for replacing an existing file.
    """
    current_file = forms.CharField(
        widget=forms.HiddenInput,
        required=False
    )
    
    replacement_reason = forms.ChoiceField(
        choices=[
            ('update', _('Content Update')),
            ('correction', _('Error Correction')),
            ('upgrade', _('Version Upgrade')),
            ('other', _('Other')),
        ],
        label=_('Replacement Reason'),
        help_text=_('Why are you replacing this file?')
    )
    
    new_file = UppyTusField(
        label=_('New File'),
        help_text=_('Select the replacement file'),
        widget_kwargs={
            'upload_type': 'tus',
            'auto_proceed': True,
            'allow_multiple': False,
            'max_files': 1,
            'height': 250,
        }
    )


class BulkUploadForm(forms.Form):
    """
    Example form for bulk file upload with metadata.
    """
    upload_batch_name = forms.CharField(
        max_length=100,
        label=_('Batch Name'),
        help_text=_('Name for this upload batch')
    )
    
    tags = forms.CharField(
        max_length=500,
        label=_('Tags'),
        required=False,
        help_text=_('Comma-separated tags for all files')
    )
    
    files = UppyMultipleFileField(
        label=_('Files'),
        help_text=_('Select multiple files to upload'),
        widget_kwargs={
            'upload_type': 's3',
            'auto_proceed': False,
            'allow_multiple': True,
            'max_files': 50,
            'max_file_size': 200 * 1024 * 1024,  # 200MB per file
            'height': 450,
            'theme': 'light',
        }
    )


# Example usage in views:
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from .uppy_forms import SingleFileUploadForm

def upload_file(request):
    if request.method == 'POST':
        form = SingleFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Process the uploaded file
            file_data = form.cleaned_data['file']
            
            # file_data contains:
            # - name: filename
            # - size: file size in bytes
            # - type: MIME type
            # - url: upload URL
            # - uploadURL: TUS upload URL (if using TUS)
            # - key: S3 object key (if using S3)
            
            # Save to database, process, etc.
            messages.success(request, 'File uploaded successfully!')
            return redirect('upload_success')
    else:
        form = SingleFileUploadForm()
    
    return render(request, 'upload.html', {'form': form})
"""
