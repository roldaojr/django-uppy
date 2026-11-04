"""
Local test superuser for manual checks in the demo admin.

    uv run python manage.py shell -c "import demo.seed_test_user"
"""

from django.contrib.auth import get_user_model

TEST_USERNAME = "uppy-test"
TEST_PASSWORD = "8mSZxjQno7Cnq5yl"

user, _ = get_user_model().objects.get_or_create(
    username=TEST_USERNAME, defaults={"is_staff": True, "is_superuser": True}
)
user.set_password(TEST_PASSWORD)
user.save()
