"""Django-тесты глобальных настроек и UI-текстов."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.platform_config.models import PlatformSettings, UIText


class PlatformConfigModelsTests(TestCase):
    """Проверяет ключевые ограничения моделей ``platform_config``.

    Параметры:
        Экземпляр класса создаётся тест-раннером Django.

    Возвращает:
        Экземпляр ``TestCase``.

    Исключения:
        AssertionError: Возникает при несоответствии ожидаемым инвариантам.

        Побочные эффекты:
            Создаёт временные записи в тестовой базе данных.
    """

    def setUp(self) -> None:
        """Подготавливает пользователя для тестов UI-текстов.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Возможны стандартные ошибки ORM при создании пользователя.

        Побочные эффекты:
            Создаёт пользователя в тестовой базе данных.
        """
        self.user = User.objects.create_user(
            email="super@example.com",
            nickname="Super",
            password="12345678",
            role=User.Role.SUPERADMIN,
            is_staff=True,
        )

    def test_only_one_active_platform_settings_record_is_allowed(self) -> None:
        """Проверяет singleton-ограничение активной записи настроек.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            IntegrityError: Ожидается при создании второй активной записи.

        Побочные эффекты:
            Создаёт тестовые записи настроек в базе данных.
        """
        PlatformSettings.objects.create(
            is_active=True,
            llm_base_url="https://example.com/v1",
        )

        with self.assertRaises(IntegrityError):
            PlatformSettings.objects.create(
                is_active=True,
                llm_base_url="https://example.org/v1",
            )

    def test_platform_settings_enforce_v1_timer_bounds(self) -> None:
        """Проверяет фиксированные границы пользовательского таймера для V1.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при выходе за согласованные границы.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        settings = PlatformSettings(
            is_active=True,
            user_timer_min_minutes=4,
            user_timer_max_minutes=20,
            llm_base_url="https://example.com/v1",
        )

        with self.assertRaises(ValidationError):
            settings.full_clean()

    def test_ui_text_cannot_store_blank_value(self) -> None:
        """Проверяет запрет на пустое значение UI-текста.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при пустом значении.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        ui_text = UIText(
            key="ui.button.logout",
            title="Выход",
            text_value="   ",
            updated_by=self.user,
        )

        with self.assertRaises(ValidationError):
            ui_text.full_clean()
