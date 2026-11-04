from types import ModuleType

from django.urls import URLPattern, path

from . import views as django_views


def uppy_urls(views: ModuleType) -> list[URLPattern]:
    """
    Upload URLs for a set of views (plain Django or REST framework).
    URL names are the same for every set, so the widget works with any of them.
    """
    return [
        # TUS protocol endpoints for resumable uploads
        path("<str:storage>", views.TusUploadView.as_view(), name="uppy-tus-upload"),
        path(
            "<str:storage>/<str:upload_id>",
            views.TusUploadView.as_view(),
            name="uppy-tus-upload",
        ),
        # Signed upload URLs of storages without S3 support
        path(
            "<str:storage>/upload/<path:filename>",
            views.UploadFileView.as_view(),
            name="uppy-file-upload",
        ),
        # S3 upload endpoint
        path(
            "<str:storage>/s3/params",
            views.UploadView.as_view(),
            name="uppy-s3-upload",
        ),
        # Uppy Companion compatible S3 multipart upload endpoints
        path(
            "<str:storage>/s3/multipart",
            views.MultipartInitView.as_view(),
            name="uppy-s3-multipart-init",
        ),
        path(
            "<str:storage>/s3/multipart/<str:upload_id>/<int:part_number>",
            views.MultipartPartView.as_view(),
            name="uppy-s3-multipart-part",
        ),
        path(
            "<str:storage>/s3/multipart/<str:upload_id>/complete",
            views.MultipartCompleteView.as_view(),
            name="uppy-s3-multipart-complete",
        ),
    ]


urlpatterns = uppy_urls(django_views)
