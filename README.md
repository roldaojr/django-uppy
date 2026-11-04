# django-uppy

Uppy upload widget and companion for Django.

## URLs

Include one of the two URL sets. URL names are the same, so the widget works with either:

```python
# Plain Django views
path("uppy/", include("django_uppy.urls"))

# REST framework views: pip install django-uppy[drf]
path("uppy/", include("django_uppy.rest_framework.urls"))
```

## Access control

The REST framework views use `REST_FRAMEWORK` authentication and permission classes.

The plain Django views use these settings:

| Setting | Default | Description |
|---|---|---|
| `UPPY_LOGIN_REQUIRED` | `True` | Requires an authenticated user |
| `UPPY_PERMISSION_REQUIRED` | `()` | Django permission, or list of permissions, the user must have |
| `UPPY_PERMISSION_CHECK` | `None` | Dotted path to a `(request, storage) -> bool` function |

```python
UPPY_PERMISSION_REQUIRED = "uploads.add_fileupload"
UPPY_PERMISSION_CHECK = "myapp.uploads.can_upload"


# myapp/uploads.py
def can_upload(request, storage):
    return storage != "bucket" or request.user.is_staff
```

Denied requests get a 403 with `{"error": "..."}`.

- `django.contrib.auth.middleware.AuthenticationMiddleware` is required, unless all three settings are off.
- While any of the settings is active, CSRF protection is enforced, so forms using the widget need `{% csrf_token %}`.
- To allow anonymous uploads, set `UPPY_LOGIN_REQUIRED = False` and leave the other two unset. The upload endpoints are then open and exempt from CSRF.
- Uploads to storages without S3 support use signed URLs (`UPPY_UPLOAD_URL_MAX_AGE`, 1 hour by default), issued only to requests that passed these checks.
