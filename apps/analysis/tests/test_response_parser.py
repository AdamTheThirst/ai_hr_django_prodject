"""Тесты парсера аналитического JSON-ответа."""

from __future__ import annotations

from unittest import TestCase

from apps.analysis.services import AnalysisResponseParser


class AnalysisResponseParserTests(TestCase):
    """Проверяет валидацию и нормализацию аналитического JSON-ответа."""

    def test_execute_returns_normalized_payload_for_valid_json(self) -> None:
        """Проверяет успешный разбор валидного ответа с игнорированием лишних полей.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = AnalysisResponseParser(
            raw_response_text='{"rating": 4, "text": "  Хороший разбор  ", "extra": "ignored"}',
            rating_min=0,
            rating_max=5,
            attempt_count=2,
        ).execute()

        self.assertTrue(result.is_valid)
        self.assertEqual(result.parsed_response.to_parsed_json_snapshot(), {"rating": 4, "text": "Хороший разбор"})
        self.assertEqual(
            result.normalized_payload,
            {
                "rating": 4,
                "text": "Хороший разбор",
                "meta": {"validation_status": "valid", "attempt_count": 2},
            },
        )

    def test_execute_marks_invalid_json_for_syntax_error(self) -> None:
        """Проверяет статус ``invalid_json`` для синтаксически битого JSON.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = AnalysisResponseParser(raw_response_text='{"rating": 4,', rating_min=0, rating_max=5).execute()

        self.assertFalse(result.is_valid)
        self.assertEqual(result.validation_status, "invalid_json")
        self.assertEqual(result.error_code, "invalid_json")

    def test_execute_rejects_non_object_json(self) -> None:
        """Проверяет запрет JSON верхнего уровня не-объектного типа.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = AnalysisResponseParser(raw_response_text='[1, 2, 3]', rating_min=0, rating_max=5).execute()

        self.assertEqual(result.validation_status, "invalid_schema")
        self.assertIn("объектом верхнего уровня", result.error_message)

    def test_execute_rejects_missing_rating(self) -> None:
        """Проверяет обработку отсутствующего обязательного поля ``rating``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = AnalysisResponseParser(raw_response_text='{"text": "ok"}', rating_min=0, rating_max=5).execute()

        self.assertEqual(result.validation_status, "invalid_schema")
        self.assertIn("rating", result.error_message)

    def test_execute_rejects_out_of_range_rating(self) -> None:
        """Проверяет обработку рейтинга вне допустимой шкалы промта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = AnalysisResponseParser(raw_response_text='{"rating": 7, "text": "ok"}', rating_min=0, rating_max=5).execute()

        self.assertEqual(result.validation_status, "invalid_schema")
        self.assertIn("[0, 5]", result.error_message)

    def test_execute_rejects_empty_text(self) -> None:
        """Проверяет обработку пустого поля ``text``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = AnalysisResponseParser(raw_response_text='{"rating": 4, "text": "   "}', rating_min=0, rating_max=5).execute()

        self.assertEqual(result.validation_status, "invalid_schema")
        self.assertIn("text", result.error_message)
