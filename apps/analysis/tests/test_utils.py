"""Pure Python тесты утилит аналитического слоя."""

from __future__ import annotations

import unittest

from apps.analysis.utils import calculate_score_totals


class AnalysisUtilsTests(unittest.TestCase):
    """Проверяет расчёт пользовательской суммы ``N из M``.

    Параметры:
        Экземпляры класса создаются ``unittest``-раннером автоматически.

    Возвращает:
        Экземпляр ``unittest.TestCase``.

    Исключения:
        AssertionError: Возникает, если сумма или максимум посчитаны неверно.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def test_calculate_score_totals_uses_only_valid_and_fallback_results(self) -> None:
        """Проверяет, что в сумму попадают только допустимые статусы.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает при неверном расчёте суммы.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        earned, maximum = calculate_score_totals(
            [
                {"rating": 4, "rating_max": 5, "validation_status": "valid"},
                {"rating": 3, "rating_max": 5, "validation_status": "fallback_saved"},
                {"rating": 2, "rating_max": 5, "validation_status": "invalid_json"},
            ]
        )

        self.assertEqual((earned, maximum), (7, 10))


if __name__ == "__main__":
    unittest.main()
