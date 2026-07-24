import json
from django.http.request import BadRequest
from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from django.core.files.storage import storages, Storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from ..settings import get_setting


@method_decorator(csrf_exempt, name="dispatch")
class BaseS3UploadView(View):
    @property
    def bucket(self):
        if not hasattr(self.storage, "bucket"):
            raise BadRequest("Invalid params")
        return self.storage.bucket

    def dispatch(self, request: HttpRequest, storage: str = None, *args, **kwargs):
        self.storage: Storage = storages[storage or "default"]
        return super().dispatch(request, *args, **kwargs)

    def get_upload_params(self, kwargs: dict):
        filename = kwargs.get("filename")
        content_type = kwargs.get("type")
        tmp_prefix = get_setting("TMP_PATH")
        upload_id = get_random_string(32)
        tmp_path = f"{tmp_prefix}/{upload_id}-{slugify(filename)}"
        return tmp_path, content_type


class UploadView(BaseS3UploadView):
    def get(self, request: HttpRequest):
        key, content_type = self.get_upload_params(request.GET)
        client = self.bucket.meta.client
        presigned_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params=dict(Bucket=self.bucket.name, Key=key, ContentType=content_type),
            ExpiresIn=3600,
        )
        return JsonResponse(
            dict(method="PUT", url=presigned_url, fields={}, headers={})
        )


class MultipartInitView(BaseS3UploadView):
    def post(self, request: HttpRequest):
        data = json.loads(request.body)
        key, _ = self.get_upload_params(data)
        bucket_object = self.bucket.Object(key)
        params = self.storage._get_write_parameters(bucket_object.key)
        upload = bucket_object.initiate_multipart_upload(**params)
        return JsonResponse({"uploadId": upload.id, "key": key})


class MultipartPartView(BaseS3UploadView):
    def get(self, request: HttpRequest, upload_id: str, part_number: int):
        key = request.GET.get("key")
        client = self.bucket.meta.client
        presigned_url = client.generate_presigned_url(
            ClientMethod="upload_part",
            Params=dict(
                Bucket=self.bucket.name,
                Key=key,
                PartNumber=part_number,
                UploadId=upload_id,
            ),
            ExpiresIn=3600,
        )
        return JsonResponse(dict(url=presigned_url))


class MultipartCompleteView(BaseS3UploadView):
    def post(self, request: HttpRequest, upload_id: str):
        key = request.GET.get("key")
        data = json.loads(request.body)
        parts = data.get("parts", [])
        if not parts:
            return JsonResponse({"error": "parts are required"}, status=400)
        client = self.bucket.meta.client
        result = client.complete_multipart_upload(
            Bucket=self.bucket.name,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        return JsonResponse(
            {
                "location": result.get("Location", ""),
                "etag": result.get("ETag", ""),
                "key": key,
            }
        )
