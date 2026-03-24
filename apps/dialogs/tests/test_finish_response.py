"""Тесты builder'а успешного ответа endpoint-а ``finish``."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest import TestCase

from apps.dialogs.services import DialogFinishDecisionService, DialogFinishResponseBuilder


class DialogFinishResponseBuilderTests(TestCase):
    """Проверяет сборку успешного response JSON для `finish`."""

    def test_execute_builds_finished_response_with_completed_analysis(self) -> None:
        """Проверяет ответ для завершённого диалога с выполненным анализом.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        response = DialogFinishResponseBuilder(
            result=SimpleNamespace(
                dialog_state=SimpleNamespace(
                    public_id="8d8e9d0c-demo",
                    status="finished",
                    ended_reason="manual_feedback",
                    user_message_count=3,
                    assistant_message_count=4,
                    effective_duration_seconds=600,
                    started_at=datetime(2026, 3, 22, 10, 6, 5),
                ),
                finish_decision=DialogFinishDecisionService(reason="manual_feedback", user_message_count=3).execute(),
                analysis_results_count=2,
            )
        ).execute()

        self.assertEqual(
            response.to_dict(),
            {
                "ok": True,
                "code": "finished",
                "message": "",
                "data": {
                    "dialog": {
                        "public_id": "8d8e9d0c-demo",
                        "status": "finished",
                        "ended_reason": "manual_feedback",
                        "user_message_count": 3,
                        "assistant_message_count": 4,
                        "seconds_remaining": 0,
                        "can_send_message": False,
                        "can_finish": False,
                        "results_url": "/dialogs/8d8e9d0c-demo/results/",
                    },
                    "analysis": {
                        "status": "completed",
                        "results_count": 2,
                    },
                    "redirect_url": "/dialogs/8d8e9d0c-demo/results/",
                },
            },
        )

    def test_execute_builds_skipped_response_without_analysis(self) -> None:
        """Проверяет контролируемый финал без пользовательских реплик.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        response = DialogFinishResponseBuilder(
            result=SimpleNamespace(
                dialog_state=SimpleNamespace(
                    public_id="dialog-skip",
                    status="analysis_skipped",
                    ended_reason="no_user_messages",
                    user_message_count=0,
                    assistant_message_count=1,
                    effective_duration_seconds=600,
                    started_at=datetime(2026, 3, 22, 10, 6, 5),
                ),
                finish_decision=DialogFinishDecisionService(reason="timeout", user_message_count=0).execute(),
                analysis_results_count=0,
            )
        ).execute()

        self.assertEqual(response.code, "analysis_skipped_no_user_messages")
        self.assertEqual(response.message, "Анализ не выполнялся, потому что пользователь не отправил ни одной реплики.")
        self.assertEqual(response.data.analysis.to_dict(), {"status": "skipped", "results_count": 0})
        self.assertEqual(response.data.redirect_url, "/dialogs/dialog-skip/results/")

    def test_execute_rejects_negative_analysis_results_count(self) -> None:
        """Проверяет запрет отрицательного числа аналитических результатов.

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
            DialogFinishResponseBuilder(
                result=SimpleNamespace(
                    dialog_state=SimpleNamespace(
                        public_id="dialog-123",
                        status="finished",
                        ended_reason="timeout",
                        user_message_count=1,
                        assistant_message_count=2,
                        effective_duration_seconds=600,
                        started_at=datetime(2026, 3, 22, 10, 6, 5),
                    ),
                    finish_decision=DialogFinishDecisionService(reason="timeout", user_message_count=1).execute(),
                    analysis_results_count=-1,
                )
            ).execute()
