from .base import BaseUploadView
from .mixins import (
    MultipartCompleteMixin,
    MultipartInitMixin,
    MultipartPartMixin,
    TusUploadMixin,
    UploadFileMixin,
    UploadParamsMixin,
)


class TusUploadView(TusUploadMixin, BaseUploadView):
    pass


class UploadView(UploadParamsMixin, BaseUploadView):
    pass


class MultipartInitView(MultipartInitMixin, BaseUploadView):
    pass


class MultipartPartView(MultipartPartMixin, BaseUploadView):
    pass


class MultipartCompleteView(MultipartCompleteMixin, BaseUploadView):
    pass


class UploadFileView(UploadFileMixin, BaseUploadView):
    pass
