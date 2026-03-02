from django.urls import path

from .views import UploadDatasetView

urlpatterns = [
    path("upload/", UploadDatasetView.as_view(), name="upload-dataset"),
]
