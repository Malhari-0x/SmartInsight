from django.urls import path

from .views import AnomalyView, ForecastView, KPIView, SegmentationView

urlpatterns = [
    path("kpi/", KPIView.as_view(), name="analytics-kpi"),
    path("forecast/", ForecastView.as_view(), name="analytics-forecast"),
    path("segment/", SegmentationView.as_view(), name="analytics-segment"),
    path("anomaly/", AnomalyView.as_view(), name="analytics-anomaly"),
]
