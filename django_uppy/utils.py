from django.core.exceptions import PermissionDenied
from django.core.signing import BadSignature, TimestampSigner
from django.utils.text import slugify

from .settings import get_setting

UPLOAD_SIGNATURE_SALT = "django_uppy.upload"


def get_file_upload_path(upload_id, filename=None, part=None):
    suffix = ""
    tmp_path = get_setting("TMP_PATH")
    if filename:
        suffix = f"-{slugify(filename)}"
    if part is not None:
        suffix = f"/part{part}"
    return f"{tmp_path}/{upload_id}{suffix}"


def _upload_signature_value(storage_name: str, filename: str) -> str:
    return f"{storage_name}:{filename}"


def sign_upload(storage_name: str, filename: str) -> str:
    """Signature (timestamp:signature) that authorizes uploading `filename`"""
    value = _upload_signature_value(storage_name, filename)
    signed = TimestampSigner(salt=UPLOAD_SIGNATURE_SALT).sign(value)
    return signed[len(value) + 1 :]


def verify_upload_signature(storage_name: str, filename: str, signature: str | None):
    """Raise PermissionDenied unless `signature` is valid and not expired"""
    if not signature:
        raise PermissionDenied("Missing upload signature")
    value = _upload_signature_value(storage_name, filename)
    try:
        TimestampSigner(salt=UPLOAD_SIGNATURE_SALT).unsign(
            f"{value}:{signature}", max_age=get_setting("UPLOAD_URL_MAX_AGE")
        )
    except BadSignature:
        raise PermissionDenied("Invalid or expired upload signature")
