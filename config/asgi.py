"""ASGI-конфигурация для запуска Django-проекта в асинхронных серверах."""

import os

from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
application = get_asgi_application()
