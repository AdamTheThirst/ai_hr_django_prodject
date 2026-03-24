"""Маршруты каркаса приложения ``content``."""

from django.urls import path

from .views import GameListPlaceholderView


app_name = "content"

urlpatterns = [
    path("", GameListPlaceholderView.as_view(), name="game-list"),
]
