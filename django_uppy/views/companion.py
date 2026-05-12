from django.views.generic import View
from django.http import HttpRequest, JsonResponse
from typing import TypedDict
from django.core.files.storage import storages, Storage
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from ..settings import get_setting


class S3Params(TypedDict):
    method: str
    url: str
    fields: dict[str, str]
    headers: dict[str, str]


class S3ParamsView(View):
    def get(self, request: HttpRequest):
        filename = request.GET.get("filename")
        upload_id = get_random_string(32)
        tmp_path = get_setting("TMP_PATH", "z-uploads.tmp").strip("/")
        filepath = f"/{tmp_path}/{upload_id}-{slugify(filename)}"
        storage: Storage = storages["default"]
        client = storage.bucket.meta.client
        presigned_url = client.generate_presigned_url(
            "put_object",
            Params={"Bucket": storage.bucket_name, "Key": filepath},
            ExpiresIn=3600,
        )
        return JsonResponse(
            S3Params(method="PUT", url=presigned_url, fields={}, headers={})
        )
