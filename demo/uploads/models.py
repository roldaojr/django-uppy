from django.db import models
from mimetypes import guess_type
from django.core.files.storage import storages


class UploadGroup(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class AbstractFileUpload(models.Model):
    group = models.ForeignKey(UploadGroup, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.file.name}"

    @property
    def content_type(self):
        mimetype = guess_type(self.file.name, strict=False)
        if mimetype is None:
            return "application/octet-stream"
        return mimetype

    def get_absolute_url(self):
        return self.file.url if self.file else None

    def delete(self, *args, **kwargs):
        if self.file and self.file.storage.exists(self.file.name):
            self.file.storage.delete(self.file.name)
        super().delete(*args, **kwargs)


class UploadedFile(AbstractFileUpload):
    file = models.FileField(upload_to="uploads/", max_length=255)


class S3FileUpload(AbstractFileUpload):
    file = models.FileField(
        upload_to="uploads/", max_length=255, storage=storages["bucket"]
    )
