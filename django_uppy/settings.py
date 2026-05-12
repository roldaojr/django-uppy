from typing import Any

from django.conf import settings as django_settings

PREFIX = "UPPY"


def get_setting(name: str, default: Any = None) -> Any:
    return getattr(django_settings, f"{PREFIX}_{name}", default)
