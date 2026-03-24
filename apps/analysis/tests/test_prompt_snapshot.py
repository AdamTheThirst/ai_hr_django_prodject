"""Тесты builder'а snapshot-полей аналитического промта."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase

from apps.analysis.services import AnalysisPromptSnapshotBuilder


class AnalysisPromptSnapshotBuilderTests(TestCase):
    """Проверяет построение snapshot-полей для `AnalysisResult`."""

    def test_execute_builds_snapshot_from_prompt_fields(self) -> None:
        """Проверяет корректное копирование всех согласованных полей промта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        snapshot = AnalysisPromptSnapshotBuilder(
            analysis_prompt=SimpleNamespace(
                sort_order=10,
                alias="focus-on-behavior",
                title="Фокус на поведении",
                header_text="Фокус на поведении, а не на личности",
                comment_text="Админская подсказка",
                min_rating=0,
                max_rating=5,
            )
        ).execute()

        self.assertEqual(
            snapshot.to_result_fields(),
            {
                "sort_order_snapshot": 10,
                "alias_snapshot": "focus-on-behavior",
                "title_snapshot": "Фокус на поведении",
                "header_snapshot_text": "Фокус на поведении, а не на личности",
                "comment_snapshot_text": "Админская подсказка",
                "rating_min": 0,
                "rating_max": 5,
            },
        )

    def test_execute_allows_blank_comment_text(self) -> None:
        """Проверяет, что комментарий snapshot может оставаться пустым.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        snapshot = AnalysisPromptSnapshotBuilder(
            analysis_prompt=SimpleNamespace(
                sort_order=0,
                alias="criterion-a",
                title="Критерий А",
                header_text="Заголовок",
                comment_text="",
                min_rating=1,
                max_rating=3,
            )
        ).execute()

        self.assertEqual(snapshot.comment_snapshot_text, "")

    def test_execute_rejects_invalid_rating_range(self) -> None:
        """Проверяет защиту от некорректного диапазона оценок промта.

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
            AnalysisPromptSnapshotBuilder(
                analysis_prompt=SimpleNamespace(
                    sort_order=1,
                    alias="criterion-a",
                    title="Критерий А",
                    header_text="Заголовок",
                    comment_text="Комментарий",
                    min_rating=5,
                    max_rating=1,
                )
            ).execute()

    def test_execute_rejects_blank_header(self) -> None:
        """Проверяет запрет пустого заголовка карточки в snapshot-полях.

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
            AnalysisPromptSnapshotBuilder(
                analysis_prompt=SimpleNamespace(
                    sort_order=1,
                    alias="criterion-a",
                    title="Критерий А",
                    header_text="   ",
                    comment_text="Комментарий",
                    min_rating=0,
                    max_rating=5,
                )
            ).execute()
