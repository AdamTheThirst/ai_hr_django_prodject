"""Тесты pure-Python policy завершения диалога."""

from __future__ import annotations

from unittest import TestCase

from apps.dialogs.services.finish_policy import (
    ANALYSIS_SKIPPED_MESSAGE,
    DialogFinishDecisionService,
)


class DialogFinishDecisionServiceTests(TestCase):
    """Проверяет согласованность решения о завершении диалога."""

    def test_manual_feedback_with_user_messages_finishes_and_starts_analysis(self) -> None:
        """Проверяет ручное завершение диалога при наличии реплик пользователя.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogFinishDecisionService(reason="manual_feedback", user_message_count=3).execute()

        self.assertEqual(result.dialog_status, "finished")
        self.assertEqual(result.ended_reason, "manual_feedback")
        self.assertEqual(result.analysis_state, "start")
        self.assertTrue(result.analysis_was_started)
        self.assertEqual(result.response_code, "finished")

    def test_timeout_with_user_messages_finishes_and_starts_analysis(self) -> None:
        """Проверяет завершение по таймеру при наличии пользовательских реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogFinishDecisionService(reason="timeout", user_message_count=1).execute()

        self.assertEqual(result.dialog_status, "finished")
        self.assertEqual(result.ended_reason, "timeout")
        self.assertTrue(result.analysis_was_started)

    def test_manual_feedback_without_user_messages_skips_analysis(self) -> None:
        """Проверяет пропуск анализа при ручном завершении без реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogFinishDecisionService(reason="manual_feedback", user_message_count=0).execute()

        self.assertEqual(result.dialog_status, "analysis_skipped")
        self.assertEqual(result.ended_reason, "no_user_messages")
        self.assertEqual(result.analysis_state, "skipped")
        self.assertFalse(result.analysis_was_started)
        self.assertEqual(result.response_code, "analysis_skipped_no_user_messages")
        self.assertEqual(result.ui_message, ANALYSIS_SKIPPED_MESSAGE)

    def test_timeout_without_user_messages_skips_analysis(self) -> None:
        """Проверяет пропуск анализа по таймеру без пользовательских реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogFinishDecisionService(reason="timeout", user_message_count=0).execute()

        self.assertEqual(result.dialog_status, "analysis_skipped")
        self.assertEqual(result.ended_reason, "no_user_messages")
        self.assertFalse(result.analysis_was_started)

    def test_constructor_rejects_invalid_reason(self) -> None:
        """Проверяет защиту от неподдерживаемой причины завершения.

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
            DialogFinishDecisionService(reason="page_leave", user_message_count=1)

    def test_constructor_rejects_negative_message_count(self) -> None:
        """Проверяет запрет отрицательного счётчика пользовательских реплик.

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
            DialogFinishDecisionService(reason="timeout", user_message_count=-1)
