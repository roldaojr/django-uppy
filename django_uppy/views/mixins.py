"""
Upload endpoints independent of the web framework.

Each mixin implements the HTTP methods of one endpoint on top of the handlers.
The concrete base view provides:
- get_request_data(): the parsed JSON body
- render(result): the response for an UploadResult
"""

from django.http import HttpRequest

from ..handlers import (
    TusHandler,
    UploadResult,
    get_local_handler,
    get_multipart_handler,
    get_tus_handler,
)


def bad_request(error: str) -> UploadResult:
    return UploadResult(status=400, data={"error": error})


class UploadParamsMixin:
    def get(self, request: HttpRequest, storage: str):
        """Get URL for single part upload"""
        handler = get_multipart_handler(storage, request)
        result = handler.upload_params(
            request.GET.get("filename"), request.GET.get("type")
        )
        return self.render(result)


class MultipartInitMixin:
    def post(self, request: HttpRequest, storage: str):
        """Initialize multipart upload"""
        data: dict = self.get_request_data()
        handler = get_multipart_handler(storage, request)
        result = handler.init_multipart(data.get("filename"), data.get("type"))
        return self.render(result)


class MultipartPartMixin:
    def get(self, request: HttpRequest, storage: str, upload_id: str, part_number: int):
        """Get URL for a part of a multipart upload"""
        key = request.GET.get("key")
        if not key:
            return self.render(bad_request("key is required"))
        handler = get_multipart_handler(storage, request)
        return self.render(handler.part_url(upload_id, part_number, key))


class MultipartCompleteMixin:
    def post(self, request: HttpRequest, storage: str, upload_id: str):
        """Complete a multipart upload"""
        key = request.GET.get("key")
        parts = self.get_request_data().get("parts", [])
        if not key:
            return self.render(bad_request("key is required"))
        if not parts:
            return self.render(bad_request("parts are required"))
        handler = get_multipart_handler(storage, request)
        return self.render(handler.complete(upload_id, key, parts))


class UploadFileMixin:
    def put(self, request: HttpRequest, storage: str, filename: str):
        """Save file uploaded to a signed URL of a local storage"""
        handler = get_local_handler(storage, request)
        result = handler.save_file(
            filename, request.GET.get("signature"), request.body
        )
        return self.render(result)


class TusUploadMixin:
    """TUS protocol endpoints"""

    def render_tus(self, result: UploadResult):
        result.headers.update(TusHandler.RESPONSE_HEADERS)
        return self.render(result)

    def options(self, request: HttpRequest, storage: str, upload_id: str = None):
        """Server capabilities"""
        return self.render_tus(get_tus_handler(storage, request).options())

    def post(self, request: HttpRequest, storage: str):
        """Create new upload"""
        handler = get_tus_handler(storage, request)
        result = handler.check_version(
            request.META.get("HTTP_TUS_RESUMABLE")
        ) or handler.create(
            request.META.get("HTTP_UPLOAD_LENGTH"),
            request.META.get("HTTP_UPLOAD_METADATA", ""),
        )
        return self.render_tus(result)

    def head(self, request: HttpRequest, storage: str, upload_id: str):
        """Upload status"""
        return self.render_tus(get_tus_handler(storage, request).status(upload_id))

    def patch(self, request: HttpRequest, storage: str, upload_id: str):
        """Upload chunk"""
        handler = get_tus_handler(storage, request)
        result = handler.check_version(
            request.META.get("HTTP_TUS_RESUMABLE")
        ) or handler.write_chunk(
            upload_id,
            request.META.get("HTTP_UPLOAD_OFFSET"),
            request.content_type,
            request.body,
        )
        return self.render_tus(result)

    def delete(self, request: HttpRequest, storage: str, upload_id: str):
        """Terminate upload"""
        return self.render_tus(get_tus_handler(storage, request).terminate(upload_id))
