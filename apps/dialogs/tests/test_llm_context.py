"""Тесты helpers для построения LLM-контекста диалога."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase

from apps.dialogs.services.llm_context import build_game_call_messages, render_analysis_transcript


class DialogLLMContextTests(TestCase):
    """Проверяет построение игровых сообщений и аналитического транскрипта."""

    def test_build_game_call_messages_uses_prompt_opening_and_sorted_history(self) -> None:
        """Проверяет нормативный порядок payload для игрового вызова.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dialog = self._build_dialog()
        messages = [
            SimpleNamespace(sequence_no=3, role="assistant", text="Добрый день."),
            SimpleNamespace(sequence_no=2, role="user", text="Здравствуйте."),
            SimpleNamespace(sequence_no=1, role="assistant", text="Привет! Начнём разговор."),
        ]

        result = build_game_call_messages(dialog=dialog, messages=messages)

        self.assertEqual(
            [message.to_payload() for message in result],
            [
                {"role": "system", "content": "Ты играешь роль сложного собеседника."},
                {"role": "assistant", "content": "Привет! Начнём разговор."},
                {"role": "user", "content": "Здравствуйте."},
                {"role": "assistant", "content": "Добрый день."},
            ],
        )

    def test_build_game_call_messages_adds_opening_when_history_starts_later(self) -> None:
        """Проверяет синтетическое добавление opening message при усечённом входе.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dialog = self._build_dialog()
        messages = [SimpleNamespace(sequence_no=2, role="user", text="Здравствуйте.")]

        result = build_game_call_messages(dialog=dialog, messages=messages)

        self.assertEqual(result[1].to_payload(), {"role": "assistant", "content": "Привет! Начнём разговор."})
        self.assertEqual(result[2].to_payload(), {"role": "user", "content": "Здравствуйте."})

    def test_build_game_call_messages_rejects_inconsistent_first_message(self) -> None:
        """Проверяет защиту от битой истории, не совпадающей со snapshot.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dialog = self._build_dialog()
        messages = [SimpleNamespace(sequence_no=1, role="assistant", text="Другая первая реплика")]

        with self.assertRaises(ValueError):
            build_game_call_messages(dialog=dialog, messages=messages)

    def test_render_analysis_transcript_formats_roles_and_header(self) -> None:
        """Проверяет рекомендуемый текстовый формат аналитического транскрипта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dialog = self._build_dialog(status="finished")
        messages = [
            SimpleNamespace(sequence_no=1, role="assistant", text="Привет! Начнём разговор."),
            SimpleNamespace(sequence_no=2, role="user", text="Здравствуйте."),
            SimpleNamespace(sequence_no=3, role="assistant", text="Расскажите подробнее."),
        ]

        transcript = render_analysis_transcript(dialog=dialog, messages=messages)

        self.assertEqual(
            transcript,
            "\n".join(
                [
                    "Игра: Я-высказывание",
                    "Сценарий: Руководитель",
                    "Статус диалога: finished",
                    "",
                    "Транскрипт:",
                    "ИИ: Привет! Начнём разговор.",
                    "Пользователь: Здравствуйте.",
                    "ИИ: Расскажите подробнее.",
                ]
            ),
        )

    def _build_dialog(self, status: str = "aborted") -> SimpleNamespace:
        """Создаёт test-double диалога с минимально нужными полями.

        Параметры:
            status: Технический код статуса диалога для транскрипта.

        Возвращает:
            ``SimpleNamespace`` с полями, совместимыми с helper-функциями.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return SimpleNamespace(
            scenario_prompt_used=SimpleNamespace(prompt_text="Ты играешь роль сложного собеседника."),
            opening_message_snapshot_text="Привет! Начнём разговор.",
            status=status,
            game=SimpleNamespace(title="Я-высказывание"),
            scenario=SimpleNamespace(title="Руководитель"),
        )
