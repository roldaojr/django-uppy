from django.core.files import File
from django.core.files.storage import storages
from django.core.files.storage.base import Storage
from django.core.signals import request_finished


class TemporaryUploadedFile(File):
    """
    A file uploaded to a temporary location (i.e. stream-to-disk).
    """

    storage: Storage
    file: File
    original_name: str
    tmp_name: str

    def __init__(self, original_name: str, tmp_name: str, *args, **kwargs):
        file = None
        if original_name and tmp_name:
            self.original_name = original_name
            self.tmp_name = tmp_name
            self.storage: Storage = storages[kwargs.pop("storage", "default")]
            file = self.storage.open(self.tmp_name, "rb")
            request_finished.connect(self.close)
        super().__init__(file, name=original_name, *args, **kwargs)

    def close(self, *args, **kwargs):
        self.file.close()
        request_finished.disconnect(self.close)
