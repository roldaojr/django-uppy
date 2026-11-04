from django.http import HttpRequest
from django.utils.module_loading import import_string

from .settings import get_setting


def get_required_permissions() -> list[str]:
    permissions = get_setting("PERMISSION_REQUIRED")
    return [permissions] if isinstance(permissions, str) else list(permissions)


def is_access_control_enabled() -> bool:
    return bool(
        get_setting("LOGIN_REQUIRED")
        or get_required_permissions()
        or get_setting("PERMISSION_CHECK")
    )


def get_access_error(request: HttpRequest, storage: str) -> str | None:
    """Error message when the request can't upload to `storage`, None if allowed"""
    if get_setting("LOGIN_REQUIRED") and not request.user.is_authenticated:
        return "Authentication required"
    if not request.user.has_perms(get_required_permissions()):
        return "Permission denied"
    permission_check = get_setting("PERMISSION_CHECK")
    if permission_check and not import_string(permission_check)(request, storage):
        return "Permission denied"
    return None
