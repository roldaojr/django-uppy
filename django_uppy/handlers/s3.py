from .base import BaseHandler
from .result import UploadResult


class S3Handler(BaseHandler):
    """Uploads straight to S3 with presigned URLs"""

    PRESIGNED_URL_EXPIRES_IN = 3600

    @property
    def bucket(self):
        return self.storage.bucket

    def _presigned_url(self, client_method: str, **params) -> str:
        return self.bucket.meta.client.generate_presigned_url(
            ClientMethod=client_method,
            Params={"Bucket": self.bucket.name, **params},
            ExpiresIn=self.PRESIGNED_URL_EXPIRES_IN,
        )

    def upload_params(self, filename: str, content_type: str) -> UploadResult:
        key = self.new_upload_key(filename)
        url = self._presigned_url("put_object", Key=key, ContentType=content_type)
        return UploadResult(
            data={"method": "PUT", "url": url, "fields": {}, "headers": {}}
        )

    def init_multipart(self, filename: str, content_type: str) -> UploadResult:
        key = self.new_upload_key(filename)
        bucket_object = self.bucket.Object(key)
        params = self.storage._get_write_parameters(bucket_object.key)
        upload = bucket_object.initiate_multipart_upload(**params)
        return UploadResult(data={"uploadId": upload.id, "key": key})

    def part_url(self, upload_id: str, part_number: int, key: str) -> UploadResult:
        url = self._presigned_url(
            "upload_part", Key=key, PartNumber=part_number, UploadId=upload_id
        )
        return UploadResult(data={"url": url})

    def complete(self, upload_id: str, key: str, parts: list) -> UploadResult:
        result: dict = self.bucket.meta.client.complete_multipart_upload(
            Bucket=self.bucket.name,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        return UploadResult(
            data={
                "location": result.get("Location", ""),
                "etag": result.get("ETag", ""),
                "key": key,
            }
        )
