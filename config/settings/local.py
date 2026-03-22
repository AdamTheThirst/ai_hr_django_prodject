"""Настройки локального окружения для разработки через ``venv``."""

from .base import *  # noqa: F403,F401
from .utils import get_bool_env, get_list_env


DEBUG = get_bool_env("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = get_list_env(
    "DJANGO_ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "0.0.0.0"],
)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
