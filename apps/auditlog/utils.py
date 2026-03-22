"""Утилиты безопасной подготовки диагностического контекста для аудита."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


SENSITIVE_CONTEXT_KEYS = {
    "password",
    "password_hash",
    "hashed_password",
    "secret",
    "secret_key",
    "api_key",
    "llm_api_key",
    "token",
    "authorization",
}
REDACTED_VALUE = "***redacted***"


def redact_sensitive_context(value):
    """Рекурсивно скрывает чувствительные значения в диагностическом JSON.

    Функция нужна для последующего использования в ``AuditLogEntry``, чтобы
    контекст логов оставался полезным для диагностики, но не сохранял
    пароли, токены и другие критичные секреты в открытом виде.

    Параметры:
        value: Произвольная JSON-подобная структура из словарей, списков,
            кортежей и простых значений.

    Возвращает:
        Новую структуру того же вида, где значения по чувствительным ключам
        заменены на безопасный маркер ``***redacted***``.

    Исключения:
        Специальные исключения не генерируются. Неизвестные типы значений
        возвращаются как есть.

    Побочные эффекты:
        Побочные эффекты отсутствуют: исходная структура не мутируется.
    """
    if isinstance(value, Mapping):
        return {
            key: REDACTED_VALUE if str(key).lower() in SENSITIVE_CONTEXT_KEYS else redact_sensitive_context(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive_context(item) for item in value]
    return value
