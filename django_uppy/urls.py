from django.urls import path
from .views.tus import TusUploadView
from .views.s3 import S3MultipartView
from .views.companion import S3ParamsView

urlpatterns = [
    # TUS protocol endpoints for resumable uploads
    path("", TusUploadView.as_view(), name="uppy-tus-upload"),
    path("<str:upload_id>", TusUploadView.as_view(), name="uppy-tus-upload"),
    # S3 parameters endpoint
    path("s3/params", S3ParamsView.as_view(), name="uppy-s3-params"),
    # Uppy Companion compatible S3 multipart upload endpoints
    path("s3/multipart", S3MultipartView.as_view(), name="uppy-s3-multipart"),
]
