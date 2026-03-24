"""Настройки production-окружения для серверного запуска проекта."""

from .base import *  # noqa: F403,F401
from .utils import get_bool_env, get_list_env


DEBUG = get_bool_env("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = get_list_env("DJANGO_ALLOWED_HOSTS", default=[])
SECURE_SSL_REDIRECT = get_bool_env("DJANGO_SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = get_bool_env("DJANGO_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = get_bool_env("DJANGO_CSRF_COOKIE_SECURE", default=False)
