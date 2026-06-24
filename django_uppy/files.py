from django.core.files import File
from django.core.files.storage import DefaultStorage
from django.core.files.storage.base import Storage
from django.core.signals import request_finished


class TemporaryUploadedFile(File):
    storage: Storage
    """
    A file uploaded to a temporary location (i.e. stream-to-disk).
    """

    def __init__(self, original_name: str, tmp_name: str, *args, **kwargs):
        file = None
        if original_name and tmp_name:
            self.original_name = original_name
            self.tmp_name = tmp_name
            storage_class = kwargs.pop("storage_class", DefaultStorage)
            self.storage = storage_class()
            file = self.storage.open(self.tmp_name, "rb")
            request_finished.connect(self.close)
        super().__init__(file, name=original_name, *args, **kwargs)

    def close(self, *args, **kwargs):
        self.file.close()
        # self.storage.delete(self.tmp_name)
        request_finished.disconnect(self.close)
