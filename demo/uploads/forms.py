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
        label="File (filesystem)",
    )

    class Meta:
        model = FileUpload
        fields = ["group", "file"]


class S3FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        widget=UppyClearableFileInput(upload_type="s3", storage="bucket"),
        label="File (S3)",
    )

    class Meta:
        model = BucketFileUpload
        fields = ["group", "file"]
