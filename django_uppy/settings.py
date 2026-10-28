from typing import Any

from django.conf import settings as django_settings

PREFIX = "UPPY"

__defaults = {
    "TMP_PATH": "z-uploads.tmp",
    "TUS_MAX_SIZE": 1024 * 1024 * 1024,  # 1GB
    "STORAGE_NAME": "default",
}


def get_setting(name: str) -> Any:
    name = name.upper()
    if name not in __defaults:
        raise ValueError(f"Invalid setting name: {name}")
    return getattr(django_settings, f"{PREFIX}_{name}", __defaults.get(name))
