"""Pure Python тесты безопасной подготовки контекста аудита."""

from __future__ import annotations

import unittest

from apps.auditlog.utils import REDACTED_VALUE, redact_sensitive_context


class AuditLogUtilsTests(unittest.TestCase):
    """Проверяет маскирование секретных значений в JSON-контексте аудита.

    Параметры:
        Экземпляры класса создаются ``unittest``-раннером автоматически.

    Возвращает:
        Экземпляр ``unittest.TestCase``.

    Исключения:
        AssertionError: Возникает, если чувствительные поля не скрываются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def test_redact_sensitive_context_masks_flat_secret_keys(self) -> None:
        """Проверяет маскирование чувствительных ключей верхнего уровня.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если ключ не был замаскирован.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = redact_sensitive_context({"password": "123", "event": "ok"})

        self.assertEqual(result["password"], REDACTED_VALUE)
        self.assertEqual(result["event"], "ok")

    def test_redact_sensitive_context_masks_nested_values(self) -> None:
        """Проверяет рекурсивное маскирование секретов во вложенных структурах.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если вложенный секрет остался открытым.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        result = redact_sensitive_context(
            {
                "payload": {
                    "api_key": "secret-key",
                    "items": [{"token": "abc"}, {"value": 42}],
                }
            }
        )

        self.assertEqual(result["payload"]["api_key"], REDACTED_VALUE)
        self.assertEqual(result["payload"]["items"][0]["token"], REDACTED_VALUE)
        self.assertEqual(result["payload"]["items"][1]["value"], 42)


if __name__ == "__main__":
    unittest.main()
