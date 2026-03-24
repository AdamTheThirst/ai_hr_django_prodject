"""Тесты builder'а DTO сообщения диалога."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import TestCase

from apps.dialogs.services import DialogMessageDTOBuilder


class DialogMessageDTOBuilderTests(TestCase):
    """Проверяет сборку JSON DTO для сообщений диалога."""

    def test_execute_builds_user_message_dto(self) -> None:
        """Проверяет корректную сериализацию пользовательского сообщения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dto = DialogMessageDTOBuilder(
            message=SimpleNamespace(
                sequence_no=2,
                role="user",
                text="Сообщение пользователя",
                char_count=22,
                created_at=datetime(2026, 3, 22, 10, 15, 12, tzinfo=timezone.utc),
            )
        ).execute()

        self.assertEqual(
            dto.to_dict(),
            {
                "sequence_no": 2,
                "role": "user",
                "text": "Сообщение пользователя",
                "char_count": 22,
                "created_at": "2026-03-22T10:15:12Z",
            },
        )

    def test_execute_builds_assistant_message_from_naive_datetime(self) -> None:
        """Проверяет форматирование naive datetime как UTC-времени.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dto = DialogMessageDTOBuilder(
            message=SimpleNamespace(
                sequence_no=3,
                role="assistant",
                text="Ответ персонажа",
                char_count=15,
                created_at=datetime(2026, 3, 22, 10, 15, 16),
            )
        ).execute()

        self.assertEqual(dto.created_at, "2026-03-22T10:15:16Z")

    def test_execute_rejects_unknown_role(self) -> None:
        """Проверяет запрет неподдерживаемой роли сообщения.

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
            DialogMessageDTOBuilder(
                message=SimpleNamespace(
                    sequence_no=1,
                    role="system",
                    text="Скрытый текст",
                    char_count=13,
                    created_at=datetime(2026, 3, 22, 10, 15, 12, tzinfo=timezone.utc),
                )
            ).execute()

    def test_execute_rejects_char_count_mismatch(self) -> None:
        """Проверяет защиту от рассинхронизации char_count и текста.

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
            DialogMessageDTOBuilder(
                message=SimpleNamespace(
                    sequence_no=1,
                    role="assistant",
                    text="Ответ",
                    char_count=3,
                    created_at=datetime(2026, 3, 22, 10, 15, 12, tzinfo=timezone.utc),
                )
            ).execute()
