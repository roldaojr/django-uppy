from django.urls import path
from .views.tus import TusUploadView
from .views import s3_compat as s3, multipart

urlpatterns = [
    # TUS protocol endpoints for resumable uploads
    path("<str:storage>", TusUploadView.as_view(), name="uppy-tus-upload"),
    path(
        "<str:storage>/<str:upload_id>", TusUploadView.as_view(), name="uppy-tus-upload"
    ),
    # S3 upload endpoint
    path("<str:storage>/s3/params", s3.UploadView.as_view(), name="uppy-s3-upload"),
    # Uppy Companion compatible S3 multipart upload endpoints
    path(
        "<str:storage>/s3/multipart",
        s3.MultipartInitView.as_view(),
        name="uppy-s3-multipart-init",
    ),
    path(
        "<str:storage>/s3/multipart/<str:upload_id>/<int:part_number>",
        s3.MultipartPartView.as_view(),
        name="uppy-s3-multipart-part",
    ),
    path(
        "<str:storage>/s3/multipart/<str:upload_id>/complete",
        s3.MultipartCompleteView.as_view(),
        name="uppy-s3-multipart-complete",
    ),
    path(
        "<str:storage>/upload/<path:filename>",
        multipart.UploadFileView.as_view(),
        name="uppy-file-upload",
    ),
]
