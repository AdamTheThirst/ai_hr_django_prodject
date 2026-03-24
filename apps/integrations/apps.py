"""Конфигурация приложения ``integrations``."""

from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    """Описывает конфигурацию внешних интеграций проекта.

    На текущем этапе приложение подготавливает отдельный модуль для будущих
    адаптеров vLLM и email, чтобы внешние сервисы не смешивались с view и
    доменной логикой других приложений.

    Параметры:
        Явные параметры не требуются.

    Возвращает:
        Экземпляр ``AppConfig`` для приложения ``integrations``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Регистрирует приложение в конфигурации Django.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations"
    verbose_name = "Интеграции"
