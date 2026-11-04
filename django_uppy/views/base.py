import json

from django.core.exceptions import BadRequest
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import View

from ..handlers import UploadResult
from ..permissions import get_access_error, is_access_control_enabled


@method_decorator(csrf_exempt, name="dispatch")
class BaseUploadView(View):
    """
    Plain Django upload view, with access controlled by the UPPY_LOGIN_REQUIRED,
    UPPY_PERMISSION_REQUIRED and UPPY_PERMISSION_CHECK settings.
    """

    # Views authorized by other means, like signed URLs
    public = False

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if self.public or not is_access_control_enabled():
            return super().dispatch(request, *args, **kwargs)
        error = get_access_error(request, kwargs["storage"])
        if error:
            return self.render(UploadResult(status=403, data={"error": error}))
        # Session authenticated requests need CSRF protection
        return csrf_protect(super().dispatch)(request, *args, **kwargs)

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
