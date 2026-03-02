import json

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dataapp.models import UploadedDataset


def _error(message, code):
    return Response({"detail": message}, status=code)


def _load_user_dataframe(user):
    dataset = UploadedDataset.objects.filter(user=user).order_by("-uploaded_at").first()
    if not dataset:
        return None, _error("No dataset uploaded yet.", status.HTTP_404_NOT_FOUND)

    try:
        import pandas as pd
    except ImportError:
        return None, _error(
            "pandas is not installed in this environment.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        df = pd.read_csv(dataset.file.path)
    except Exception as exc:
        return None, _error(f"Unable to read dataset: {exc}", status.HTTP_400_BAD_REQUEST)

    if df.empty:
        return None, _error("Uploaded dataset is empty.", status.HTTP_400_BAD_REQUEST)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df, None


def _validate_columns(df, required_columns):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return _error(
            f"Missing required columns: {', '.join(missing)}",
            status.HTTP_400_BAD_REQUEST,
        )
    return None


class KPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df, error_response = _load_user_dataframe(request.user)
        if error_response:
            return error_response
        error_response = _validate_columns(df, ["sales"])
        if error_response:
            return error_response

        import pandas as pd

        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df = df.dropna(subset=["sales"])
        if df.empty:
            return _error(
                "Column 'sales' does not contain valid numeric values.",
                status.HTTP_400_BAD_REQUEST,
            )

        total_revenue = float(df["sales"].sum())
        avg_sales = float(df["sales"].mean())

        if "month" in df.columns:
            monthly = (
                df.groupby("month")["sales"]
                .sum()
                .sort_index()
                .astype(float)
                .to_dict()
            )
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            monthly = (
                df.groupby(df["date"].dt.to_period("M").astype(str))["sales"]
                .sum()
                .sort_index()
                .astype(float)
                .to_dict()
            )
        else:
            monthly = {}

        return Response(
            {
                "total_revenue": total_revenue,
                "avg_sales": avg_sales,
                "row_count": int(len(df)),
                "monthly_sales": monthly,
            }
        )


class ForecastView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df, error_response = _load_user_dataframe(request.user)
        if error_response:
            return error_response
        error_response = _validate_columns(df, ["date", "sales"])
        if error_response:
            return error_response

        import pandas as pd

        try:
            from prophet import Prophet
        except ImportError:
            return _error(
                "prophet is not installed in this environment.",
                status.HTTP_501_NOT_IMPLEMENTED,
            )

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df = df.dropna(subset=["date", "sales"]).sort_values("date")

        if len(df) < 2:
            return _error(
                "Forecasting needs at least 2 valid date/sales rows.",
                status.HTTP_400_BAD_REQUEST,
            )

        periods = request.query_params.get("periods", 30)
        try:
            periods = max(1, min(int(periods), 365))
        except ValueError:
            periods = 30

        train_df = df.rename(columns={"date": "ds", "sales": "y"})[["ds", "y"]]
        model = Prophet()
        model.fit(train_df)
        future = model.make_future_dataframe(periods=periods, freq="D")
        forecast = model.predict(future)

        result = forecast[["ds", "yhat"]].tail(periods).copy()
        result["ds"] = result["ds"].dt.strftime("%Y-%m-%d")
        result["yhat"] = result["yhat"].round(2)

        return Response(result.to_dict(orient="records"))


class SegmentationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df, error_response = _load_user_dataframe(request.user)
        if error_response:
            return error_response
        error_response = _validate_columns(df, ["customer_id", "sales"])
        if error_response:
            return error_response

        import pandas as pd

        try:
            from sklearn.cluster import KMeans
        except ImportError:
            return _error(
                "scikit-learn is not installed in this environment.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df = df.dropna(subset=["customer_id", "sales"])
        if df.empty:
            return _error(
                "No valid customer_id/sales rows found.",
                status.HTTP_400_BAD_REQUEST,
            )

        rfm = (
            df.groupby("customer_id", as_index=False)
            .agg(total_sales=("sales", "sum"), order_count=("customer_id", "count"))
            .sort_values("total_sales", ascending=False)
        )
        if len(rfm) < 2:
            return _error(
                "Segmentation needs at least 2 unique customers.",
                status.HTTP_400_BAD_REQUEST,
            )

        n_clusters = min(3, len(rfm))
        kmeans = KMeans(n_clusters=n_clusters, n_init="auto", random_state=42)
        rfm["cluster"] = kmeans.fit_predict(rfm[["total_sales", "order_count"]])

        return Response(json.loads(rfm.to_json(orient="records")))


class AnomalyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df, error_response = _load_user_dataframe(request.user)
        if error_response:
            return error_response
        error_response = _validate_columns(df, ["sales"])
        if error_response:
            return error_response

        import pandas as pd

        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            return _error(
                "scikit-learn is not installed in this environment.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df = df.dropna(subset=["sales"])
        if len(df) < 5:
            return _error(
                "Anomaly detection needs at least 5 numeric sales rows.",
                status.HTTP_400_BAD_REQUEST,
            )

        model = IsolationForest(contamination="auto", random_state=42)
        df["anomaly"] = model.fit_predict(df[["sales"]])
        anomalies = df[df["anomaly"] == -1]

        return Response(
            {
                "anomaly_count": int(len(anomalies)),
                "records": json.loads(anomalies.to_json(orient="records")),
            }
        )
