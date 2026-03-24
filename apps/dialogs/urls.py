"""Маршруты каркаса приложения ``dialogs``."""

from django.urls import path

from .views import DialogsPlaceholderView


app_name = "dialogs"

urlpatterns = [
    path("", DialogsPlaceholderView.as_view(), name="placeholder"),
]
