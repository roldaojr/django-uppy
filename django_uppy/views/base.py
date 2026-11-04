import json

from django.core.exceptions import BadRequest
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from ..handlers import UploadResult


@method_decorator(csrf_exempt, name="dispatch")
class BaseUploadView(View):
    """Plain Django upload view, without authentication"""

    def get_request_data(self) -> dict:
        try:
            return json.loads(self.request.body)
        except json.JSONDecodeError:
            raise BadRequest("Invalid JSON body")

    def render(self, result: UploadResult) -> HttpResponse:
        if result.data is not None:
            return JsonResponse(
                result.data, status=result.status, headers=result.headers
            )
        return HttpResponse(
            result.content, status=result.status, headers=result.headers
        )
