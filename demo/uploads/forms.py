from django import forms
from .models import UploadGroup, UploadedFile, S3FileUpload
from django_uppy.widgets import UppyWidget


class UploadGroupForm(forms.ModelForm):
    class Meta:
        model = UploadGroup
        fields = ["name"]


class UploadedFileForm(forms.ModelForm):
    file = forms.FileField(widget=UppyWidget(), label="File (filesystem)")

    class Meta:
        model = UploadedFile
        fields = ["file", "group"]


class S3FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        widget=UppyWidget(upload_type="s3", storage="bucket"), label="File (S3)"
    )

    class Meta:
        model = S3FileUpload
        fields = ["file", "group"]
