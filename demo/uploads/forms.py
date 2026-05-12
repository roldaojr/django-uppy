from django import forms
from .models import UploadGroup, UploadedFile
from django_uppy.widgets import UppyWidget


class UploadGroupForm(forms.ModelForm):
    class Meta:
        model = UploadGroup
        fields = ["name"]


class UploadedFileForm(forms.ModelForm):
    file = forms.FileField(widget=UppyWidget())

    class Meta:
        model = UploadedFile
        fields = ["file", "group"]
