from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UploadGroup,
    BucketFileUpload,
    FileUpload,
    TusFileUpload,
    S3FileUpload,
)
from .forms import TusFileUploadForm, S3FileUploadForm


class UploadedFileInline(admin.TabularInline):
    model = TusFileUpload
    form = TusFileUploadForm
    extra = 1


@admin.register(UploadGroup)
class UploadGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)


class BaseFileUploadAdmin(admin.ModelAdmin):
    list_display = ("file", "content_type_display", "file_link")

    def content_type_display(self, obj):
        return obj.content_type

    content_type_display.short_description = "Content Type"

    def file_link(self, obj):
        if obj.file and obj.file.url:
            return format_html(
                '<a href="{}" target="_blank">View File</a>', obj.file.url
            )
        return "No file"

    file_link.short_description = "File Link"
    file_link.allow_tags = True


@admin.register(FileUpload)
class ClassicFileUploadAdmin(BaseFileUploadAdmin):
    pass


@admin.register(BucketFileUpload)
class BucketFileUploadAdmin(BaseFileUploadAdmin):
    pass


@admin.register(TusFileUpload)
class UploadedFileAdmin(BaseFileUploadAdmin):
    form = TusFileUploadForm


@admin.register(S3FileUpload)
class S3FileUploadAdmin(BaseFileUploadAdmin):
    form = S3FileUploadForm
