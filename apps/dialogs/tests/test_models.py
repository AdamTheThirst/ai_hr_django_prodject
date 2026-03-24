"""Django-тесты моделей диалога."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.content.models import Game, Scenario, ScenarioPrompt
from apps.dialogs.models import DialogMessage, DialogSession


class DialogModelsTests(TestCase):
    """Проверяет ключевые ограничения моделей диалога.

    Параметры:
        Экземпляр класса создаётся Django test runner.

    Возвращает:
        Экземпляр ``TestCase``.

    Исключения:
        AssertionError: Возникает при несоответствии ожидаемым инвариантам.

    Побочные эффекты:
        Создаёт тестовые записи в базе данных.
    """

    def setUp(self) -> None:
        """Подготавливает пользователя, игру, сценарий и промт для тестов.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Возможны стандартные ошибки ORM при создании фикстур.

        Побочные эффекты:
            Создаёт фикстурные записи в базе данных.
        """
        self.user = User.objects.create_user(
            email="dialog-user@example.com",
            nickname="Диалог",
            password="12345678",
        )
        self.game = Game.objects.create(slug="game-1", title="Игра", sort_order=1)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="scenario-1",
            title="Сценарий",
            conditions_text="Условия",
            opening_message_text="Привет",
            sort_order=1,
        )
        self.prompt = ScenarioPrompt.objects.create(
            scenario=self.scenario,
            title="Промт",
            prompt_text="Игровой промт",
            is_active=True,
        )

    def build_dialog(self, status: str = DialogSession.Status.ACTIVE, ended_reason: str = "") -> DialogSession:
        """Создаёт несохранённый объект диалога с базовыми snapshot-значениями.

        Параметры:
            status: Желаемый статус диалога.
            ended_reason: Желаемая причина завершения.

        Возвращает:
            Несохранённый объект ``DialogSession``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют, так как объект не сохраняется.
        """
        return DialogSession(
            user=self.user,
            game=self.game,
            scenario=self.scenario,
            scenario_prompt_used=self.prompt,
            status=status,
            started_at=timezone.now(),
            ended_at=None,
            ended_reason=ended_reason,
            effective_duration_seconds=600,
            effective_user_message_max_chars=2500,
            effective_game_reply_max_chars=2500,
            effective_analysis_reply_max_chars=5000,
            effective_llm_model_name="Qwen/Qwen3-32B",
            effective_llm_temperature=Decimal("0.70"),
            effective_llm_top_p=Decimal("0.80"),
            effective_llm_game_max_tokens=1024,
            effective_llm_analysis_max_tokens=1024,
            conditions_snapshot_text="Условия",
            opening_message_snapshot_text="Привет",
        )

    def test_only_one_active_dialog_per_user_is_allowed(self) -> None:
        """Проверяет ограничение на единственный активный диалог пользователя.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            IntegrityError: Ожидается при создании второго active-диалога.

        Побочные эффекты:
            Создаёт тестовые записи диалогов в базе данных.
        """
        self.build_dialog().save()

        with self.assertRaises(IntegrityError):
            self.build_dialog().save()

    def test_finished_dialog_requires_valid_reason_and_end_timestamp(self) -> None:
        """Проверяет согласованность статуса finished с причиной и временем.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при пустом ended_at.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dialog = self.build_dialog(status=DialogSession.Status.FINISHED, ended_reason=DialogSession.EndedReason.MANUAL_FEEDBACK)

        with self.assertRaises(ValidationError):
            dialog.full_clean()

    def test_user_message_cannot_exceed_frozen_limit(self) -> None:
        """Проверяет серверный лимит длины пользовательского сообщения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при превышении лимита.

        Побочные эффекты:
            Создаёт запись диалога в базе данных.
        """
        dialog = self.build_dialog()
        dialog.save()
        message = DialogMessage(
            dialog=dialog,
            sequence_no=1,
            role=DialogMessage.Role.USER,
            text="x" * 2501,
            char_count=2501,
        )

        with self.assertRaises(ValidationError):
            message.full_clean()
