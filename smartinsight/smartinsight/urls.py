from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from dashboard.views import DashboardHomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/dashboard/favicon.svg", permanent=False),
    ),
    path("", DashboardHomeView.as_view(), name="home"),
    path("api/data/", include("dataapp.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
