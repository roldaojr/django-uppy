import json
import math
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
from django.db.models.fields.files import FieldFile
from django.urls import reverse
from .settings import get_setting
from .files import TemporaryUploadedFile


class UppyClearableFileInput(ClearableFileInput):
    """
    Django widget for Uppy file uploader with TUS and S3 multipart support.
    """

    template_name = "uppy/clearable_file_input.html"
    is_multipart = True
    error_messages = {"invalid_file": "Invalid file metadata"}

    class Media:
        js = [
            "django-uppy/uppy.min.js",
            "django-uppy/single-file-input-plugin.js",
            "django-uppy/file-input-widget.js",
        ]
        css = {
            "screen": ["django-uppy/uppy.min.css"],
        }

    def __init__(
        self,
        upload_type="tus",  # 'tus' or 's3'
        storage="default",
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
        self.max_file_size = max_file_size or get_setting("TUS_MAX_SIZE")
        self.allowed_file_types = allowed_file_types
        self.inline = inline
        self.height = height
        self.theme = theme
        self.storage_name = storage

    def value_from_datadict(self, data, files, name):
        filename = data.get(name, "")
        if not filename:
            return

        if "//" not in filename:
            raise ValidationError(
                self.error_messages["invalid_file"],
                code="invalid_file",
            )

        upload_id, original_name = filename.split("//")
        tmp_name = f"{get_setting('TMP_PATH')}/{upload_id}"
        upload = TemporaryUploadedFile(
            original_name, tmp_name, storage=self.storage_name
        )
        return upload

    def get_context(self, name, value: FieldFile | None, attrs: dict):
        context: dict = super().get_context(name, value, attrs)
        input_id = attrs.get("id", f"id_{name}")
        uppy_id = "uppy_" + input_id
        config = self._get_config()
        plugins = self._get_plugins(uppy_id)
        # Update context
        context.update(
            {
                "uppy": {
                    "id": uppy_id,
                    "target_id": input_id,
                    "config": json.dumps(config),
                    "plugins": json.dumps(plugins),
                }
            }
        )
        return context

    def _get_config(self) -> dict:
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
        return uppy_config

    def _get_plugins(self, uppy_id: str) -> dict:
        plugins = {}
        plugins.update(self._get_ui_plugin(uppy_id))
        # Upload plugin based on type
        upload_params = {
            "endpoint": reverse(
                "uppy-tus-upload", kwargs={"storage": self.storage_name}
            ),
            "retryDelays": [0, 1000, 3000, 5000],
        }
        if self.upload_type == "tus":
            plugins["Tus"] = upload_params
        elif self.upload_type == "s3":
            plugins["AwsS3"] = upload_params
        return plugins

    def _get_ui_plugin(self, uppy_id: str):
        return {
            "SingleFileInput": {
                "target": f"#{uppy_id}",
            }
        }

    def _get_dashboard_plugin(self, uppy_id: str):
        return {
            "Dashboard": {
                "inline": self.inline,
                "target": f"#{uppy_id}",
                "height": self.height,
                "showProgressDetails": True,
                "hideUploadButton": True,
                "hideProgressAfterFinish": True,
                "doneButtonHandler": False,
                "disableThumbnailGenerator": True,
                "theme": self.theme,
                "note": f"Upload files. Max {self.max_files} files, max {self._format_size(self.max_file_size)} per file.",
            }
        }

    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 bytes"
        size_name = ("bytes", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"
