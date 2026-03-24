"""Pure-Python builder DTO сообщения диалога для JSON-ответов."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from apps.core.services.contracts import BaseService


class DialogMessageLike(Protocol):
    """Описывает минимальный контракт сообщения диалога для DTO-builder'а.

    Protocol позволяет строить JSON DTO как из ORM-модели `DialogMessage`,
    так и из тестовых объектов без загрузки Django ORM.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с обязательными полями сообщения диалога.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    sequence_no: int
    role: str
    text: str
    char_count: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DialogMessageDTO:
    """Хранит JSON-представление одного сообщения диалога.

    DTO соответствует контракту `user_message` / `assistant_message` из
    API-спеки и нужен, чтобы runtime-сервисы возвращали единый формат без
    дублирования сериализации по разным endpoint-ам.

    Параметры:
        sequence_no: Порядковый номер сообщения в диалоге.
        role: Роль сообщения `user` или `assistant`.
        text: Текст сообщения.
        char_count: Количество символов в тексте.
        created_at: Время создания в ISO 8601.

    Возвращает:
        Экземпляр `DialogMessageDTO`.

    Исключения:
        ValueError: Возникает при пустом тексте, неподдерживаемой роли,
            невалидном `sequence_no` или несовпадении `char_count`.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    sequence_no: int
    role: str
    text: str
    char_count: int
    created_at: str

    def __post_init__(self) -> None:
        """Проверяет базовую согласованность DTO сообщения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при нарушении инвариантов сообщения.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.sequence_no < 1:
            raise ValueError("sequence_no должен быть положительным.")
        if self.role not in {"user", "assistant"}:
            raise ValueError("role должен быть user или assistant.")
        if not self.text.strip():
            raise ValueError("text не может быть пустым.")
        if self.char_count != len(self.text):
            raise ValueError("char_count должен совпадать с фактической длиной text.")
        if not self.created_at.strip():
            raise ValueError("created_at не может быть пустым.")

    def to_dict(self) -> dict[str, Any]:
        """Преобразует DTO в словарь для JSON-сериализации.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь, совпадающий по форме с контрактом API для сообщения.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "sequence_no": self.sequence_no,
            "role": self.role,
            "text": self.text,
            "char_count": self.char_count,
            "created_at": self.created_at,
        }


class DialogMessageDTOBuilder(BaseService[DialogMessageDTO]):
    """Строит JSON DTO одного сообщения диалога.

    Сервис инкапсулирует форматирование времени в ISO 8601, проверку роли и
    длины текста, чтобы runtime-endpoint-ы `send-message` и будущие API не
    сериализовали сообщения вручную в нескольких местах.

    Параметры:
        message: Объект, совместимый с `DialogMessageLike`.

    Возвращает:
        Экземпляр `DialogMessageDTO`.

    Исключения:
        ValueError: Возникает при невалидных полях сообщения.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(self, *, message: DialogMessageLike) -> None:
        """Сохраняет сообщение-источник для последующего построения DTO.

        Параметры:
            message: Сообщение диалога или совместимый test-double.

        Возвращает:
            ``None``.

        Исключения:
            Специальные исключения не генерируются на этапе инициализации.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.message = message

    def execute(self) -> DialogMessageDTO:
        """Строит DTO сообщения в формате runtime JSON-контракта.

        Параметры:
            Явные параметры отсутствуют; используется сообщение конструктора.

        Возвращает:
            Экземпляр `DialogMessageDTO`.

        Исключения:
            ValueError: Возникает при невалидных полях сообщения.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return DialogMessageDTO(
            sequence_no=int(self.message.sequence_no),
            role=str(self.message.role),
            text=str(self.message.text),
            char_count=int(self.message.char_count),
            created_at=_format_datetime_iso8601(self.message.created_at),
        )


def _format_datetime_iso8601(value: datetime) -> str:
    """Форматирует `datetime` в ISO 8601 с суффиксом `Z` для UTC.

    Параметры:
        value: Дата и время создания сообщения.

    Возвращает:
        Строку ISO 8601, пригодную для JSON-контракта API.

    Исключения:
        ValueError: Возникает, если вместо `datetime` передано иное значение.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    if not isinstance(value, datetime):
        raise ValueError("created_at должен быть экземпляром datetime.")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")
