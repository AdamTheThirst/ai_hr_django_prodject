"""Django-тесты моделей контентного слоя."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt, SystemPrompt


class ContentModelsTests(TestCase):
    """Проверяет ключевые ограничения моделей ``content``.

    Параметры:
        Экземпляр класса создаётся тест-раннером Django.

    Возвращает:
        Экземпляр ``TestCase``.

    Исключения:
        AssertionError: Возникает при несовпадении фактического и ожидаемого
            поведения моделей.

    Побочные эффекты:
        Создаёт временные записи в тестовой базе данных.
    """

    def setUp(self) -> None:
        """Подготавливает базовые объекты пользователя, игры и сценария.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Возможны стандартные ошибки ORM при создании фикстур.

        Побочные эффекты:
            Создаёт тестовые записи в базе данных.
        """
        self.author = User.objects.create_user(
            email="content-admin@example.com",
            nickname="Контент",
            password="12345678",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.game = Game.objects.create(
            slug="feedback-game",
            title="Игра",
            short_description="Описание",
            sort_order=1,
            is_published=True,
            created_by=self.author,
        )
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="scenario-a",
            title="Сценарий",
            short_description="Описание",
            conditions_text="Условия",
            opening_message_text="Привет",
            sort_order=1,
            is_published=True,
            created_by=self.author,
        )

    def test_scenario_prompt_allows_only_one_active_prompt_per_scenario(self) -> None:
        """Проверяет ограничение на единственный активный игровой промт.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            IntegrityError: Ожидается при создании второй активной версии.

        Побочные эффекты:
            Создаёт тестовые записи промтов в базе данных.
        """
        ScenarioPrompt.objects.create(
            scenario=self.scenario,
            title="v1",
            prompt_text="Текст 1",
            is_active=True,
            created_by=self.author,
        )

        with self.assertRaises(IntegrityError):
            ScenarioPrompt.objects.create(
                scenario=self.scenario,
                title="v2",
                prompt_text="Текст 2",
                is_active=True,
                created_by=self.author,
            )

    def test_analysis_prompt_validates_rating_range(self) -> None:
        """Проверяет запрет на диапазон рейтинга с min больше max.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при некорректном диапазоне.

        Побочные эффекты:
            Побочные эффекты отсутствуют, так как объект не сохраняется.
        """
        prompt = AnalysisPrompt(
            game=self.game,
            alias="criterion-a",
            title="Критерий",
            header_text="Заголовок",
            prompt_text="Анализируй",
            sort_order=1,
            min_rating=5,
            max_rating=4,
            created_by=self.author,
        )

        with self.assertRaises(ValidationError):
            prompt.full_clean()

    def test_system_prompt_cannot_be_archived_and_active(self) -> None:
        """Проверяет запрет на активный архивный системный промт.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при несогласованном состоянии.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        prompt = SystemPrompt(
            key="analysis_metadata_generator",
            title="Служебный промт",
            prompt_text="Текст",
            is_active=True,
            is_archived=True,
            created_by=self.author,
        )

        with self.assertRaises(ValidationError):
            prompt.full_clean()
