from django import forms
from .models import UploadGroup, BucketFileUpload, FileUpload
from django_uppy.widgets import UppyClearableFileInput


class UploadGroupForm(forms.ModelForm):
    class Meta:
        model = UploadGroup
        fields = ["name"]


class TusFileUploadForm(forms.ModelForm):
    file = forms.FileField(
        widget=UppyClearableFileInput(),
        label="File (TUS)",
    )

    class Meta:
        model = FileUpload
        fields = ["group", "file"]


class MultipartUploadForm(TusFileUploadForm):
    file = forms.FileField(
        widget=UppyClearableFileInput(),
        label="File (multipart/filesystem)",
    )


class S3FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        widget=UppyClearableFileInput(storage="bucket"),
        label="File (S3)",
    )

    class Meta:
        model = BucketFileUpload
        fields = ["group", "file"]
