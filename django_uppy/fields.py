import json
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import Field
from django.utils.translation import gettext_lazy as _

from .widgets import UppyWidget, UppyDashboardWidget


class UppyFileField(Field):
    """
    Django form field for Uppy file uploads.
    Handles both TUS and S3 multipart uploads.
    """

    widget = UppyWidget

    def __init__(
        self,
        upload_type="tus",
        max_files=5,
        max_file_size=None,
        allowed_file_types=None,
        **kwargs,
    ):
        self.upload_type = upload_type
        self.max_files = max_files
        self.max_file_size = max_file_size
        self.allowed_file_types = allowed_file_types

        # Configure widget with field parameters
        widget_kwargs = {
            "upload_type": upload_type,
            "max_files": max_files,
            "max_file_size": max_file_size,
            "allowed_file_types": allowed_file_types,
        }
        widget_kwargs.update(kwargs.pop("widget_kwargs", {}))

        kwargs.setdefault("widget", self.widget(**widget_kwargs))
        super().__init__(**kwargs)

    def to_python(self, value):
        """Convert JSON string from widget to Python data"""
        if not value:
            return None

        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                raise ValidationError(_("Invalid file data format"))

        return value

    def validate(self, value):
        """Validate uploaded file data"""
        if value is None:
            if self.required:
                raise ValidationError(_("This field is required"))
            return

        if isinstance(value, dict):
            # Single file validation
            self._validate_single_file(value)
        elif isinstance(value, list):
            # Multiple files validation
            if len(value) > self.max_files:
                raise ValidationError(_(f"Maximum {self.max_files} files allowed"))

            for file_data in value:
                self._validate_single_file(file_data)
        else:
            raise ValidationError(_("Invalid file data format"))

    def _validate_single_file(self, file_data):
        """Validate a single file data"""
        if not isinstance(file_data, dict):
            raise ValidationError(_("Invalid file data format"))

        # Check required fields
        required_fields = ["name", "size", "type"]
        for field in required_fields:
            if field not in file_data:
                raise ValidationError(_(f"Missing required field: {field}"))

        # Validate file size
        if self.max_file_size and file_data["size"] > self.max_file_size:
            raise ValidationError(_(f"File size exceeds maximum allowed size"))

        # Validate file type
        if self.allowed_file_types:
            file_extension = file_data["name"].split(".")[-1].lower()
            if file_extension not in self.allowed_file_types:
                raise ValidationError(_(f"File type not allowed"))

    def clean(self, value):
        """Clean and return the file data"""
        value = super().clean(value)

        if value is None:
            return None

        # For Django model integration, we might need to convert to UploadedFile
        # This depends on the specific use case
        return value


class UppyModelField(models.FileField):
    """
    Django model field that works with Uppy uploads.
    Stores the file path and handles Uppy upload responses.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 500)
        super().__init__(**kwargs)

    def from_db_value(self, value, expression, connection):
        """Convert database value to Python object"""
        if value is None:
            return None
        return value

    def pre_save(self, model_instance, add):
        """Handle file upload before saving to database"""
        value = getattr(model_instance, self.name)

        if value is None:
            return None

        # Handle Uppy file data
        if isinstance(value, dict):
            # Extract file URL or path from Uppy response
            file_url = value.get("url") or value.get("uploadURL")
            if file_url:
                # For S3 uploads, store the key/path
                if "key" in value:
                    setattr(model_instance, self.name, value["key"])
                else:
                    # For TUS uploads, extract path from URL
                    setattr(model_instance, self.name, file_url)
            else:
                raise ValidationError(_("No file URL provided in upload response"))

        return super().pre_save(model_instance, add)

    def formfield(self, **kwargs):
        """Return form field for this model field"""
        kwargs.setdefault("form_class", UppyFileField)
        return super().formfield(**kwargs)


class UppyMultipleFileField(UppyFileField):
    """
    Django form field for multiple Uppy file uploads.
    """

    widget = UppyDashboardWidget  # Dashboard is better for multiple files

    def __init__(self, **kwargs):
        kwargs.setdefault("max_files", 10)
        super().__init__(**kwargs)

    def to_python(self, value):
        """Convert JSON string to list of file data"""
        if not value:
            return []

        if isinstance(value, str):
            try:
                data = json.loads(value)
                if isinstance(data, dict):
                    return [data]  # Single file wrapped in list
                elif isinstance(data, list):
                    return data
                else:
                    raise ValidationError(_("Invalid file data format"))
            except (json.JSONDecodeError, ValueError):
                raise ValidationError(_("Invalid file data format"))

        if isinstance(value, dict):
            return [value]

        return value


class UppyImageField(UppyFileField):
    """
    Specialized Uppy field for image uploads.
    """

    def __init__(self, **kwargs):
        # Default to image file types
        kwargs.setdefault("allowed_file_types", ["jpg", "jpeg", "png", "gif", "webp"])
        kwargs.setdefault("widget", UppyDashboardWidget)
        super().__init__(**kwargs)

    def validate(self, value):
        """Validate that uploaded files are images"""
        super().validate(value)

        if value is None:
            return

        files = value if isinstance(value, list) else [value]

        for file_data in files:
            # Check MIME type
            mime_type = file_data.get("type", "")
            if not mime_type.startswith("image/"):
                raise ValidationError(_("Only image files are allowed"))


class UppyDocumentField(UppyFileField):
    """
    Specialized Uppy field for document uploads.
    """

    def __init__(self, **kwargs):
        # Default to common document file types
        kwargs.setdefault(
            "allowed_file_types",
            [
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                "ppt",
                "pptx",
                "txt",
                "rtf",
                "odt",
                "ods",
                "odp",
            ],
        )
        super().__init__(**kwargs)


# Convenience field classes
class UppyTusField(UppyFileField):
    """Uppy field using TUS protocol"""

    def __init__(self, **kwargs):
        kwargs.setdefault("upload_type", "tus")
        super().__init__(**kwargs)


class UppyS3Field(UppyFileField):
    """Uppy field using S3 multipart upload"""

    def __init__(self, **kwargs):
        kwargs.setdefault("upload_type", "s3")
        super().__init__(**kwargs)


class UppyTusImageField(UppyImageField):
    """Uppy image field using TUS protocol"""

    def __init__(self, **kwargs):
        kwargs.setdefault("upload_type", "tus")
        super().__init__(**kwargs)


class UppyS3ImageField(UppyImageField):
    """Uppy image field using S3 multipart upload"""

    def __init__(self, **kwargs):
        kwargs.setdefault("upload_type", "s3")
        super().__init__(**kwargs)
