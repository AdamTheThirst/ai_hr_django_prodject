"""Тесты pure-Python policy покидания страницы диалога."""

from __future__ import annotations

from unittest import TestCase

from apps.dialogs.services.abandon_policy import DialogAbandonDecisionService


class DialogAbandonDecisionServiceTests(TestCase):
    """Проверяет логику abandon-сценария для активного диалога."""

    def test_page_leave_with_user_messages_aborts_and_starts_analysis(self) -> None:
        """Проверяет покидание страницы при наличии пользовательских реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogAbandonDecisionService(reason="page_leave", user_message_count=2).execute()

        self.assertEqual(result.dialog_status, "aborted")
        self.assertEqual(result.ended_reason, "page_leave")
        self.assertEqual(result.analysis_state, "start")
        self.assertTrue(result.analysis_was_started)

    def test_inactive_timeout_with_user_messages_aborts_and_starts_analysis(self) -> None:
        """Проверяет server-side добивание неактивного диалога при наличии реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogAbandonDecisionService(reason="inactive_timeout", user_message_count=1).execute()

        self.assertEqual(result.dialog_status, "aborted")
        self.assertEqual(result.ended_reason, "inactive_timeout")
        self.assertTrue(result.analysis_was_started)

    def test_page_leave_without_user_messages_aborts_and_skips_analysis(self) -> None:
        """Проверяет пропуск анализа при abandon без пользовательских реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogAbandonDecisionService(reason="page_leave", user_message_count=0).execute()

        self.assertEqual(result.dialog_status, "aborted")
        self.assertEqual(result.ended_reason, "page_leave")
        self.assertEqual(result.analysis_state, "skipped")
        self.assertFalse(result.analysis_was_started)

    def test_inactive_timeout_without_user_messages_aborts_and_skips_analysis(self) -> None:
        """Проверяет пропуск анализа при серверном inactive-timeout без реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = DialogAbandonDecisionService(reason="inactive_timeout", user_message_count=0).execute()

        self.assertEqual(result.dialog_status, "aborted")
        self.assertEqual(result.ended_reason, "inactive_timeout")
        self.assertFalse(result.analysis_was_started)

    def test_constructor_rejects_invalid_reason(self) -> None:
        """Проверяет защиту от неподдерживаемой причины abandon-сценария.

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
            DialogAbandonDecisionService(reason="manual_feedback", user_message_count=1)

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
            DialogAbandonDecisionService(reason="page_leave", user_message_count=-1)
