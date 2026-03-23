"""Тесты builder'а payload ответа ``send-message``."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import TestCase

from apps.dialogs.services import DialogSendMessagePayloadBuilder


class DialogSendMessagePayloadBuilderTests(TestCase):
    """Проверяет сборку блока ``data`` для успешного ответа `send-message`."""

    def test_execute_builds_payload_matching_api_contract(self) -> None:
        """Проверяет полную сборку payload с диалогом и двумя сообщениями.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        started_at = datetime(2026, 3, 22, 10, 6, 5)
        payload = DialogSendMessagePayloadBuilder(
            result=SimpleNamespace(
                dialog_state=SimpleNamespace(
                    public_id="8d8e9d0c-demo",
                    status="active",
                    ended_reason="",
                    user_message_count=1,
                    assistant_message_count=2,
                    effective_duration_seconds=600,
                    started_at=started_at,
                ),
                user_message=SimpleNamespace(
                    sequence_no=2,
                    role="user",
                    text="Сообщение пользователя",
                    char_count=22,
                    created_at=datetime(2026, 3, 22, 10, 15, 12, tzinfo=timezone.utc),
                ),
                assistant_message=SimpleNamespace(
                    sequence_no=3,
                    role="assistant",
                    text="Ответ персонажа",
                    char_count=15,
                    created_at=datetime(2026, 3, 22, 10, 15, 16),
                ),
            ),
            now_provider=lambda: started_at + timedelta(seconds=53),
        ).execute()

        self.assertEqual(
            payload.to_dict(),
            {
                "dialog": {
                    "public_id": "8d8e9d0c-demo",
                    "status": "active",
                    "ended_reason": None,
                    "user_message_count": 1,
                    "assistant_message_count": 2,
                    "seconds_remaining": 547,
                    "can_send_message": True,
                    "can_finish": True,
                    "results_url": "/dialogs/8d8e9d0c-demo/results/",
                },
                "user_message": {
                    "sequence_no": 2,
                    "role": "user",
                    "text": "Сообщение пользователя",
                    "char_count": 22,
                    "created_at": "2026-03-22T10:15:12Z",
                },
                "assistant_message": {
                    "sequence_no": 3,
                    "role": "assistant",
                    "text": "Ответ персонажа",
                    "char_count": 15,
                    "created_at": "2026-03-22T10:15:16Z",
                },
            },
        )

    def test_execute_rejects_swapped_message_roles(self) -> None:
        """Проверяет защиту от перепутанных ролей `user` и `assistant`.

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
            DialogSendMessagePayloadBuilder(
                result=SimpleNamespace(
                    dialog_state=SimpleNamespace(
                        public_id="dialog-123",
                        status="active",
                        ended_reason="",
                        user_message_count=1,
                        assistant_message_count=2,
                        effective_duration_seconds=600,
                        started_at=datetime(2026, 3, 23, 10, 0, 0),
                    ),
                    user_message=SimpleNamespace(
                        sequence_no=2,
                        role="assistant",
                        text="Неверная роль",
                        char_count=13,
                        created_at=datetime(2026, 3, 22, 10, 15, 12, tzinfo=timezone.utc),
                    ),
                    assistant_message=SimpleNamespace(
                        sequence_no=3,
                        role="user",
                        text="Тоже неверная роль",
                        char_count=18,
                        created_at=datetime(2026, 3, 22, 10, 15, 16, tzinfo=timezone.utc),
                    ),
                )
            ).execute()
