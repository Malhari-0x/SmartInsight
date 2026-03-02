from rest_framework import serializers

from .models import UploadedDataset


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedDataset
        fields = ["id", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]
