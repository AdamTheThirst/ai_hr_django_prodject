"""Маршруты технического и стартового уровня проекта."""

from django.urls import path

from .views import HealthCheckView, HomePageView


app_name = "core"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("health/", HealthCheckView.as_view(), name="health"),
]
