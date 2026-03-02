from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser

from .models import UploadedDataset
from .serializers import DatasetSerializer


class UploadDatasetView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        datasets = UploadedDataset.objects.filter(user=request.user).order_by("-uploaded_at")
        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DatasetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = serializer.save(user=request.user)

        cleanup_note = "Uploaded successfully."
        try:
            import pandas as pd

            df = pd.read_csv(dataset.file.path)
            df.dropna(how="all", inplace=True)
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            df.to_csv(dataset.file.path, index=False)
            cleanup_note = "Uploaded and normalized column names."
        except ImportError:
            cleanup_note = "Uploaded. Install pandas to enable normalization."
        except Exception as exc:
            cleanup_note = f"Uploaded. Normalization skipped: {exc}"

        return Response(
            {
                "id": dataset.id,
                "file": dataset.file.name,
                "message": cleanup_note,
            },
            status=status.HTTP_201_CREATED,
        )
