import json

from django.http import HttpRequest, JsonResponse
from django.http.request import BadRequest

from .base import BaseUploadView


class BaseS3UploadView(BaseUploadView):
    @property
    def bucket(self):
        if not hasattr(self.storage, "bucket"):
            raise BadRequest("Invalid params")
        return self.storage.bucket


class UploadView(BaseS3UploadView):
    def get(self, request: HttpRequest):
        key, content_type = self.get_upload_params(request.GET)
        client = self.bucket.meta.client
        presigned_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket.name,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )
        return JsonResponse(
            {"method": "PUT", "url": presigned_url, "fields": {}, "headers": {}}
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
            Params={
                "Bucket": self.bucket.name,
                "Key": key,
                "PartNumber": part_number,
                "UploadId": upload_id,
            },
            ExpiresIn=3600,
        )
        return JsonResponse({"url": presigned_url})


class MultipartCompleteView(BaseS3UploadView):
    def post(self, request: HttpRequest, upload_id: str):
        key = request.GET.get("key")
        data = json.loads(request.body)
        parts = data.get("parts", [])
        if not parts:
            return JsonResponse({"error": "parts are required"}, status=400)
        client = self.bucket.meta.client
        result: dict = client.complete_multipart_upload(
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
