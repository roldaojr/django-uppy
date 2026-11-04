from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.middleware.csrf import CSRF_SECRET_LENGTH
from django.test import Client, TestCase, override_settings
from django.urls import reverse

CSRF_TOKEN = "a" * CSRF_SECRET_LENGTH
TUS_HEADERS = {"HTTP_TUS_RESUMABLE": "1.0.0", "HTTP_UPLOAD_LENGTH": "5"}
PERMISSION_NAME = "auth.add_user"


def only_default_storage(request, storage: str) -> bool:
    return storage == "default"


def params_url(storage: str = "default") -> str:
    return reverse("uppy-s3-upload", args=[storage])


def tus_url() -> str:
    return reverse("uppy-tus-upload", args=["default"])


@override_settings(UPPY_LOGIN_REQUIRED=True)
class AccessControlTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("uploader")

    def get_params(self, storage: str = "default"):
        return self.client.get(
            params_url(storage), {"filename": "photo.jpg", "type": "image/jpeg"}
        )


class LoginRequiredTest(AccessControlTestCase):
    def assert_authentication_required(self, response):
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"error": "Authentication required"})

    def test_anonymous_is_denied(self):
        init_url = reverse("uppy-s3-multipart-init", args=["default"])

        self.assert_authentication_required(self.get_params())
        self.assert_authentication_required(self.client.post(tus_url(), **TUS_HEADERS))
        self.assert_authentication_required(self.client.post(init_url))

    def test_authenticated_user_is_allowed(self):
        self.client.force_login(self.user)

        self.assertEqual(self.get_params().status_code, 200)
        self.assertEqual(self.client.post(tus_url(), **TUS_HEADERS).status_code, 201)

    def test_login_is_required_by_default(self):
        with self.settings():
            del settings.UPPY_LOGIN_REQUIRED
            self.assert_authentication_required(self.get_params())

    def test_unknown_storage_is_denied_before_lookup(self):
        self.assert_authentication_required(self.get_params("unknown"))


@override_settings(UPPY_PERMISSION_REQUIRED=PERMISSION_NAME)
class PermissionRequiredTest(AccessControlTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_user_without_permission_is_denied(self):
        response = self.get_params()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"error": "Permission denied"})

    def test_user_with_permission_is_allowed(self):
        app_label, codename = PERMISSION_NAME.split(".")
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        )

        self.assertEqual(self.get_params().status_code, 200)


@override_settings(
    UPPY_PERMISSION_CHECK="django_uppy.tests.test_access_control.only_default_storage"
)
class PermissionCheckTest(AccessControlTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_check_allows_storage(self):
        self.assertEqual(self.get_params("default").status_code, 200)

    def test_check_denies_storage(self):
        response = self.get_params("bucket")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"error": "Permission denied"})


class CsrfTest(AccessControlTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.client.cookies[settings.CSRF_COOKIE_NAME] = CSRF_TOKEN

    def test_post_without_token_is_denied(self):
        response = self.client.post(tus_url(), **TUS_HEADERS)

        self.assertEqual(response.status_code, 403)

    def test_post_with_token_is_allowed(self):
        response = self.client.post(
            tus_url(), HTTP_X_CSRFTOKEN=CSRF_TOKEN, **TUS_HEADERS
        )

        self.assertEqual(response.status_code, 201)


class SignedUploadTest(AccessControlTestCase):
    def put(self, url: str):
        return self.client.put(url, b"content", content_type="application/octet-stream")

    def get_upload_url(self) -> str:
        self.client.force_login(self.user)
        url = self.get_params().json()["url"]
        self.client.logout()
        return url

    def test_signature_authorizes_anonymous_upload(self):
        self.assertEqual(self.put(self.get_upload_url()).status_code, 200)

    def test_anonymous_upload_without_signature_is_denied(self):
        url = self.get_upload_url().split("?")[0]

        self.assertEqual(self.put(url).status_code, 403)
