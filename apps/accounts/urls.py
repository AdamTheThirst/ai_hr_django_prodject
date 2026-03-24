"""Маршруты каркаса приложения ``accounts``."""

from django.urls import path

from .views import LoginPlaceholderView


app_name = "accounts"

urlpatterns = [
    path("login/", LoginPlaceholderView.as_view(), name="login"),
]
