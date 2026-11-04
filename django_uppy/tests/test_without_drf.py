import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Blocks the rest_framework import, then loads the plain upload views and URLs
CHECK_SCRIPT = """
import sys
sys.modules["rest_framework"] = None

import django
django.setup()

import django_uppy.views
import django_uppy.widgets
from django.urls import reverse

print(reverse("uppy-tus-upload", args=["default"]))
"""


class WithoutRestFrameworkTest(SimpleTestCase):
    def test_views_work_without_rest_framework(self):
        env = {**os.environ, "DJANGO_SETTINGS_MODULE": "demo.test_settings"}
        result = subprocess.run(
            [sys.executable, "-c", CHECK_SCRIPT],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "/uppy/default")
