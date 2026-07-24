from django.http import HttpRequest
from django.views import View
from django.core.files.storage import storages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from . import s3, multipart


@method_decorator(csrf_exempt, name="dispatch")
class BaseView(View):
    s3_view_class = None
    compat_view_class = None
    proxied_view: View

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        storage = storages[kwargs.get("storage", "default")]
        if hasattr(storage, "bucket"):
            self.proxied_view = self.s3_view_class()
        else:
            self.proxied_view = self.compat_view_class()
        self.proxied_view.setup(request, *args, **kwargs)
        return self.proxied_view.dispatch(request, *args, **kwargs)


class UploadView(BaseView):
    s3_view_class = s3.UploadView
    compat_view_class = multipart.UploadView


class MultipartInitView(BaseView):
    s3_view_class = s3.MultipartInitView
    compat_view_class = multipart.MultipartInitView


class MultipartPartView(BaseView):
    s3_view_class = s3.MultipartPartView
    compat_view_class = multipart.MultipartPartView


class MultipartCompleteView(BaseView):
    s3_view_class = s3.MultipartCompleteView
    compat_view_class = multipart.MultipartCompleteView
