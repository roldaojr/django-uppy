import hashlib
from urllib.parse import quote

from django.core.files.storage import storages, Storage
from django.http import HttpRequest
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from ..utils import get_file_upload_path
from ..settings import get_setting


class S3MultipartView(APIView):
    """
    Uppy Companion compatible S3 multipart upload endpoints.
    Compatible with @uppy/aws-s3 plugin.
    """

    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = get_setting("PERMISSION_CLASSES", [])
    storage: Storage = storages[get_setting("STORAGE_NAME", "default")]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if S3 storage
        self.is_s3 = hasattr(self.storage, "bucket")

    def get(self, request: HttpRequest, *args, **kwargs):
        """Initiate multipart upload"""
        filename = request.GET.get("filename")
        part_count = request.GET.get("partCount")
        file_type = request.GET.get("type", "")
        if not filename:
            return Response({"error": "filename is required"}, status=400)
        if not part_count:
            return Response({"error": "partCount is required"}, status=400)
        try:
            part_count = int(part_count)
        except ValueError:
            return Response({"error": "Invalid partCount"}, status=400)

        if self.is_s3:
            return self._init_s3_multipart(filename, part_count, file_type, request)
        else:
            return self._init_local_multipart(filename, part_count, file_type, request)

    def post(self, request: HttpRequest, *args, **kwargs):
        """Complete multipart upload"""
        upload_id = request.GET.get("uploadId")
        filename = request.GET.get("filename")

        if not upload_id:
            return Response({"error": "uploadId is required"}, status=400)

        if self.is_s3:
            return self._complete_s3_multipart(upload_id, filename, request.data)
        else:
            return self._complete_local_multipart(upload_id, filename, request.data)

    def delete(self, request: HttpRequest, *args, **kwargs):
        """Abort multipart upload"""
        upload_id = request.GET.get("uploadId")
        filename = request.GET.get("filename")

        if not upload_id:
            return Response({"error": "uploadId is required"}, status=400)

        if self.is_s3:
            return self._abort_s3_multipart(upload_id, filename)
        else:
            return self._abort_local_multipart(upload_id, filename)

    def _init_s3_multipart(self, filename, part_count, file_type, request):
        """Initialize S3 multipart upload"""
        try:
            # Generate unique key
            upload_id = get_random_string(32)
            key = f"uploads/{upload_id}/{quote(filename)}"

            # Create S3 multipart upload
            bucket_object = self.storage.bucket.Object(key)
            upload = bucket_object.initiate_multipart_upload(
                ContentType=file_type,
                **self.storage._get_write_parameters(bucket_object.key),
            )

            # Generate presigned URLs for each part
            upload_urls = []
            for part_num in range(1, part_count + 1):
                url = self.storage.connection.meta.client.generate_presigned_url(
                    ClientMethod="upload_part",
                    Params={
                        "Bucket": upload.bucket_name,
                        "Key": upload.object_key,
                        "PartNumber": part_num,
                        "UploadId": upload.id,
                    },
                    ExpiresIn=3600,
                )
                upload_urls.append(url)

            # Generate complete URL
            complete_url = self.request.build_absolute_uri(
                f"{reverse('uppy-s3-multipart')}?uploadId={upload.id}&filename={quote(filename)}"
            )

            return Response(
                {
                    "uploadId": upload.id,
                    "key": key,
                    "parts_urls": upload_urls,
                    "complete_url": complete_url,
                },
                headers={"Cache-control": "no-cache"},
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def _init_local_multipart(self, filename, part_count, file_type, request):
        """Initialize local multipart upload"""
        try:
            upload_id = get_random_string(32)

            # Generate upload URLs for local storage
            upload_urls = []
            for part_num in range(1, part_count + 1):
                url = request.build_absolute_uri(
                    f"{reverse('uppy-s3-multipart')}?uploadId={upload_id}&partNumber={part_num}&filename={quote(filename)}"
                )
                upload_urls.append(url)

            # Generate complete URL
            complete_url = request.build_absolute_uri(
                f"{reverse('uppy-s3-multipart')}?uploadId={upload_id}&filename={quote(filename)}"
            )

            return Response(
                {
                    "uploadId": upload_id,
                    "parts_urls": upload_urls,
                    "complete_url": complete_url,
                },
                headers={"Cache-control": "no-cache"},
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def _complete_s3_multipart(self, upload_id, filename, data):
        """Complete S3 multipart upload"""
        try:
            parts = data.get("parts", [])
            if not parts:
                return Response({"error": "parts are required"}, status=400)

            # Find the key for this upload
            # This is a simplified approach - in production you'd want to track this
            key = f"uploads/{upload_id.split('-')[0]}/{quote(filename)}"

            # Complete multipart upload
            result = self.storage.connection.meta.client.complete_multipart_upload(
                Bucket=self.storage.bucket.name,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

            return Response(
                {
                    "location": result.get("Location", ""),
                    "etag": result.get("ETag", ""),
                    "key": key,
                }
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def _complete_local_multipart(self, upload_id, filename, data):
        """Complete local multipart upload"""
        try:
            parts = data.get("parts", [])
            if not parts:
                return Response({"error": "parts are required"}, status=400)

            # Combine parts into final file
            final_path = get_file_upload_path(upload_id, filename=filename)

            with self.storage.open(final_path, "wb+") as final_file:
                for part_num in range(1, len(parts) + 1):
                    part_path = get_file_upload_path(upload_id, part=part_num)
                    if self.storage.exists(part_path):
                        with self.storage.open(part_path, "rb") as part_file:
                            final_file.write(part_file.read())
                        self.storage.delete(part_path)

            # Clean up
            self.storage.delete(get_file_upload_path(upload_id))

            return Response(
                {
                    "location": self.storage.url(final_path),
                    "key": final_path,
                }
            )

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def _abort_s3_multipart(self, upload_id, filename):
        """Abort S3 multipart upload"""
        try:
            # Find the key for this upload
            key = f"uploads/{upload_id.split('-')[0]}/{quote(filename)}"

            self.storage.connection.meta.client.abort_multipart_upload(
                Bucket=self.storage.bucket.name, Key=key, UploadId=upload_id
            )

            return Response(status=204)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def _abort_local_multipart(self, upload_id, filename):
        """Abort local multipart upload"""
        try:
            # Clean up all parts
            for part_num in range(1, 100):  # Reasonable limit
                part_path = get_file_upload_path(upload_id, part=part_num)
                if self.storage.exists(part_path):
                    self.storage.delete(part_path)

            # Clean up upload info
            self.storage.delete(get_file_upload_path(upload_id))

            return Response(status=204)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def put(self, request, *args, **kwargs):
        """Handle part upload for local storage"""
        if self.is_s3:
            return Response(
                {"error": "Direct part upload not supported for S3"}, status=400
            )

        upload_id = request.GET.get("uploadId")
        part_number = request.GET.get("partNumber")
        filename = request.GET.get("filename")

        if not all([upload_id, part_number, filename]):
            return Response(
                {"error": "uploadId, partNumber, and filename are required"}, status=400
            )

        try:
            part_number = int(part_number)
        except ValueError:
            return Response({"error": "Invalid partNumber"}, status=400)

        try:
            # Save part
            part_path = get_file_upload_path(upload_id, part=part_number)
            if "file" in request.FILES:
                self.storage.save(part_path, request.FILES["file"])
            else:
                self.storage.save(part_path, request.body)

            return Response({"etag": hashlib.md5(request.body).hexdigest()})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
