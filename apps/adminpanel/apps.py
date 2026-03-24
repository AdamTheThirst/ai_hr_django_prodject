"""Конфигурация приложения ``adminpanel``."""

from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    """Описывает конфигурацию пользовательской административной панели.

    Приложение резервирует отдельный модуль под внутренний backoffice,
    который будет реализован позднее отдельно от стандартного Django Admin.

    Параметры:
        Явные параметры не требуются.

    Возвращает:
        Экземпляр ``AppConfig`` для приложения ``adminpanel``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Регистрирует приложение в реестре Django.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.adminpanel"
    verbose_name = "Внутренняя админ-панель"
