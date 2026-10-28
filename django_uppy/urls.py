from django.urls import path
from django.views.generic import View

from .views import multipart
from .views import s3_compat as s3
from .views.tus import TusUploadView


def s3_upload_urls(
    single_upload: View,
    init_multipart: View,
    upload_part: View,
    complete_multipart: View,
    prefix: str = "uppy-s3",
):
    return [
        # S3 upload endpoint
        path(
            "<str:storage>/s3/params",
            single_upload.as_view(),
            name=f"{prefix}-upload",
        ),
        # Uppy Companion compatible S3 multipart upload endpoints
        path(
            "<str:storage>/s3/multipart",
            init_multipart.as_view(),
            name=f"{prefix}-multipart-init",
        ),
        path(
            "<str:storage>/s3/multipart/<str:upload_id>/<int:part_number>",
            upload_part.as_view(),
            name=f"{prefix}-multipart-part",
        ),
        path(
            "<str:storage>/s3/multipart/<str:upload_id>/complete",
            complete_multipart.as_view(),
            name=f"{prefix}-multipart-complete",
        ),
    ]


urlpatterns = [
    # TUS protocol endpoints for resumable uploads
    path("<str:storage>", TusUploadView.as_view(), name="uppy-tus-upload"),
    path(
        "<str:storage>/<str:upload_id>", TusUploadView.as_view(), name="uppy-tus-upload"
    ),
    path(
        "<str:storage>/upload/<path:filename>",
        multipart.UploadFileView.as_view(),
        name="uppy-file-upload",
    ),
] + s3_upload_urls(
    s3.UploadView,
    s3.MultipartInitView,
    s3.MultipartPartView,
    s3.MultipartCompleteView,
)
