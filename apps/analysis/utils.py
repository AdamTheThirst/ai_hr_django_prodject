"""Pure Python утилиты аналитического слоя."""

from __future__ import annotations

from collections.abc import Iterable


class ScoreTotals(tuple):
    """Хранит рассчитанную пользовательскую сумму и возможный максимум.

    Параметры:
        Кортеж создаётся через функцию ``calculate_score_totals`` и содержит
        два значения: набранную сумму и максимально возможную сумму.

    Возвращает:
        Неизменяемый кортеж ``(earned, maximum)``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """


def calculate_score_totals(results: Iterable[dict]) -> tuple[int, int]:
    """Считает пользовательскую сумму ``N из M`` по сохранённым результатам.

    Функция реализует зафиксированное в спецификации правило: сумма берётся
    как ``sum(rating)``, а максимум — как ``sum(rating_max)`` только по тем
    результатам, которые считаются валидными или сохранёнными для показа.

    Параметры:
        results: Итерируемая коллекция словарей с ключами ``rating``,
            ``rating_max`` и ``validation_status``.

    Возвращает:
        Кортеж из двух целых чисел: набранная сумма и максимальная сумма.

    Исключения:
        KeyError: Может возникнуть, если входной словарь не содержит
            обязательных ключей.
        TypeError: Может возникнуть, если значения не поддерживают сложение.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    valid_statuses = {"valid", "fallback_saved"}
    earned = 0
    maximum = 0
    for item in results:
        if item["validation_status"] not in valid_statuses:
            continue
        earned += int(item["rating"])
        maximum += int(item["rating_max"])
    return earned, maximum
