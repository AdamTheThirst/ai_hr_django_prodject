"""Маршруты каркаса приложения ``adminpanel``."""

from django.urls import path

from .views import BackofficePlaceholderView


app_name = "adminpanel"

urlpatterns = [
    path("", BackofficePlaceholderView.as_view(), name="dashboard"),
]
