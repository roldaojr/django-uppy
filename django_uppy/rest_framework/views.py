from django.http import HttpResponse
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from ..handlers import UploadResult
from ..views.mixins import (
    MultipartCompleteMixin,
    MultipartInitMixin,
    MultipartPartMixin,
    TusUploadMixin,
    UploadFileMixin,
    UploadParamsMixin,
)


class BaseAPIUploadView(APIView):
    """
    Upload view using REST framework authentication and permissions,
    from DEFAULT_AUTHENTICATION_CLASSES / DEFAULT_PERMISSION_CLASSES unless overridden.
    """

    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    def get_request_data(self) -> dict:
        return self.request.data

    def render(self, result: UploadResult) -> HttpResponse:
        if result.data is not None:
            return Response(result.data, status=result.status, headers=result.headers)
        return HttpResponse(
            result.content, status=result.status, headers=result.headers
        )


class TusUploadView(TusUploadMixin, BaseAPIUploadView):
    pass


class UploadView(UploadParamsMixin, BaseAPIUploadView):
    pass


class MultipartInitView(MultipartInitMixin, BaseAPIUploadView):
    pass


class MultipartPartView(MultipartPartMixin, BaseAPIUploadView):
    pass


class MultipartCompleteView(MultipartCompleteMixin, BaseAPIUploadView):
    pass


class UploadFileView(UploadFileMixin, BaseAPIUploadView):
    # Authorized by the signed URL issued by the other (authenticated) views
    authentication_classes = []
    permission_classes = [AllowAny]
