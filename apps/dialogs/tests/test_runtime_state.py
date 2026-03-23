"""Тесты builder'а runtime-состояния диалога."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import TestCase

from apps.dialogs.services import DialogRuntimeStateBuilder


class DialogRuntimeStateBuilderTests(TestCase):
    """Проверяет сборку `dialog_state` по JSON-контракту API."""

    def test_execute_builds_active_state_with_remaining_seconds(self) -> None:
        """Проверяет active-состояние с расчётом оставшегося таймера.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        started_at = datetime(2026, 3, 23, 10, 0, 0)
        state = DialogRuntimeStateBuilder(
            dialog=self._build_dialog(started_at=started_at),
            now_provider=lambda: started_at + timedelta(seconds=53),
        ).execute()

        self.assertEqual(
            state.to_dict(),
            {
                "public_id": "dialog-123",
                "status": "active",
                "ended_reason": None,
                "user_message_count": 1,
                "assistant_message_count": 2,
                "seconds_remaining": 547,
                "can_send_message": True,
                "can_finish": True,
                "results_url": "/dialogs/dialog-123/results/",
            },
        )

    def test_execute_builds_finished_state_with_zero_seconds(self) -> None:
        """Проверяет финальное состояние диалога после завершения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        state = DialogRuntimeStateBuilder(
            dialog=self._build_dialog(status="finished", ended_reason="manual_feedback"),
        ).execute()

        self.assertEqual(state.status, "finished")
        self.assertEqual(state.ended_reason, "manual_feedback")
        self.assertEqual(state.seconds_remaining, 0)
        self.assertFalse(state.can_send_message)
        self.assertFalse(state.can_finish)

    def test_execute_never_returns_negative_seconds(self) -> None:
        """Проверяет отсечение таймера на нуле после истечения времени.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        started_at = datetime(2026, 3, 23, 10, 0, 0)
        state = DialogRuntimeStateBuilder(
            dialog=self._build_dialog(started_at=started_at),
            now_provider=lambda: started_at + timedelta(seconds=900),
        ).execute()

        self.assertEqual(state.seconds_remaining, 0)

    def test_execute_rejects_negative_user_message_count(self) -> None:
        """Проверяет защиту от отрицательного счётчика сообщений пользователя.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        with self.assertRaises(ValueError):
            DialogRuntimeStateBuilder(dialog=self._build_dialog(user_message_count=-1)).execute()

    def _build_dialog(
        self,
        *,
        status: str = "active",
        ended_reason: str = "",
        user_message_count: int = 1,
        assistant_message_count: int = 2,
        started_at: datetime | None = None,
    ) -> SimpleNamespace:
        """Создаёт test-double диалога с минимально нужными runtime-полями.

        Параметры:
            status: Статус диалога.
            ended_reason: Причина завершения.
            user_message_count: Счётчик пользовательских реплик.
            assistant_message_count: Счётчик реплик assistant.
            started_at: Время начала диалога.

        Возвращает:
            `SimpleNamespace` с полями, совместимыми с builder'ом.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return SimpleNamespace(
            public_id="dialog-123",
            status=status,
            ended_reason=ended_reason,
            user_message_count=user_message_count,
            assistant_message_count=assistant_message_count,
            effective_duration_seconds=600,
            started_at=started_at or datetime(2026, 3, 23, 10, 0, 0),
        )
