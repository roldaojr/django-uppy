from django.contrib import admin
from django.utils.html import format_html
from .models import UploadedFile, UploadGroup
from .forms import UploadedFileForm


class UploadedFileInline(admin.TabularInline):
    model = UploadedFile
    form = UploadedFileForm
    extra = 1


@admin.register(UploadGroup)
class UploadGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [UploadedFileInline]


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("file", "content_type_display", "file_link")
    form = UploadedFileForm

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
