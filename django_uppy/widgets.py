import json
import math
from django.conf import settings as django_settings
from django.forms.widgets import Widget
from django.urls import reverse

from . import settings


class UppyWidget(Widget):
    """
    Django widget for Uppy file uploader with TUS and S3 multipart support.
    """

    template_name = "uppy/widget.html"
    is_multipart = True

    def __init__(
        self,
        upload_type="tus",  # 'tus' or 's3'
        auto_proceed=False,
        allow_multiple=False,
        max_files=1,
        max_file_size=None,
        allowed_file_types=None,
        inline=True,
        height=300,
        theme="minimal",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.upload_type = upload_type
        self.auto_proceed = auto_proceed
        self.allow_multiple = allow_multiple
        self.max_files = max_files
        self.max_file_size = max_file_size or settings.get_setting(
            "TUS_MAX_SIZE", 1024 * 1024 * 1024
        )  # 1GB default
        self.allowed_file_types = allowed_file_types
        self.inline = inline
        self.height = height
        self.theme = theme

    def get_context(self, name, value, attrs: dict):
        context = super().get_context(name, value, attrs)
        # Generate unique ID for this widget instance
        input_id = attrs.get("id", f"id_{name}")
        uppy_id = "uppy_" + input_id

        # Uppy configuration
        uppy_config = {
            "debug": django_settings.DEBUG,
            "autoProceed": self.auto_proceed,
            "allowMultipleUploadBatches": self.allow_multiple,
            "restrictions": {
                "maxNumberOfFiles": self.max_files,
                "maxFileSize": self.max_file_size,
            },
        }
        if self.allowed_file_types:
            uppy_config["restrictions"]["allowedFileTypes"] = self.allowed_file_types

        # Plugin configuration
        plugins = {
            "Dashboard": {
                "inline": self.inline,
                "target": f"#{uppy_id}",
                "height": self.height,
                "showProgressDetails": True,
                "hideUploadButton": True,
                "hideProgressAfterFinish": True,
                "doneButtonHandler": False,
                "theme": self.theme,
                "note": f"Upload files. Max {self.max_files} files, max {self._format_size(self.max_file_size)} per file.",
            },
        }

        # Upload plugin based on type
        upload_params = {
            "endpoint": reverse("uppy-tus-upload"),
            "retryDelays": [0, 1000, 3000, 5000],
        }
        if self.upload_type == "tus":
            plugins["Tus"] = upload_params
        elif self.upload_type == "s3":
            plugins["AwsS3"] = upload_params

        # Update context
        context.update(
            {
                "uppy": {
                    "id": uppy_id,
                    "target_id": input_id,
                    "config": json.dumps(uppy_config),
                    "plugins": json.dumps(plugins),
                },
                "upload_type": self.upload_type,
                "value": value,
                "is_initial": bool(value),
            }
        )

        return context

    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 bytes"
        size_name = ("bytes", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"


class UppyDashboardWidget(UppyWidget):
    """
    Uppy widget with Dashboard UI for better user experience.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("inline", True)
        kwargs.setdefault("height", 350)
        super().__init__(**kwargs)


class UppyDragDropWidget(UppyWidget):
    """
    Uppy widget with simple drag and drop area.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("inline", False)
        kwargs.setdefault("target", ".uppy-drag-drop")
        super().__init__(**kwargs)


class UppyInlineWidget(UppyWidget):
    """
    Uppy widget optimized for inline forms.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("inline", True)
        kwargs.setdefault("height", 200)
        kwargs.setdefault("theme", "minimal")
        kwargs.setdefault("auto_proceed", True)
        super().__init__(**kwargs)
