from django.urls import include, path

urlpatterns = [
    path("uppy/", include("django_uppy.rest_framework.urls")),
]
