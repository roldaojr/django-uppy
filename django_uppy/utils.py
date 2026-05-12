from django.utils.text import slugify

from .settings import get_setting


def get_file_upload_path(upload_id, filename=None, part=None):
    suffix = "/"
    tmp_path = get_setting("TMP_PATH", "z-uploads.tmp")
    if filename:
        slugname = slugify(filename)
        suffix = f"_{slugname}"
    if part is not None:
        suffix = f"/part{part}"
    return f"{tmp_path}/{upload_id}{suffix}"
