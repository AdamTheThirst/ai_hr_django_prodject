"""Pure-Python builder runtime-состояния диалога для JSON-ответов."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Protocol
from uuid import UUID

from apps.core.services.contracts import BaseService


class DialogStateLike(Protocol):
    """Описывает минимальный контракт диалога для runtime builder'а.

    Protocol позволяет строить runtime-представление как из ORM-модели
    `DialogSession`, так и из тестовых объектов без загрузки Django ORM.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с полями, нужными для JSON-контракта диалога.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    public_id: UUID | str
    status: str
    ended_reason: str
    user_message_count: int
    assistant_message_count: int
    effective_duration_seconds: int
    started_at: datetime


@dataclass(frozen=True, slots=True)
class DialogRuntimeState:
    """Хранит runtime-состояние диалога для JSON-ответов веб-слоя.

    DTO соответствует форме `data.dialog` из API-спеки и позволяет
    прикладным сервисам отдавать единый словарь состояния независимо от того,
    какой сценарий обновляет диалог: отправка сообщения, finish или abandon.

    Параметры:
        public_id: Публичный идентификатор диалога.
        status: Текущий статус диалога.
        ended_reason: Причина завершения или пустая строка/`None`.
        user_message_count: Количество реплик пользователя.
        assistant_message_count: Количество реплик assistant.
        seconds_remaining: Оставшееся время таймера.
        can_send_message: Разрешена ли отправка нового сообщения.
        can_finish: Разрешено ли ручное завершение.
        results_url: URL экрана результатов по диалогу.

    Возвращает:
        Экземпляр `DialogRuntimeState`.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    public_id: str
    status: str
    ended_reason: str | None
    user_message_count: int
    assistant_message_count: int
    seconds_remaining: int
    can_send_message: bool
    can_finish: bool
    results_url: str

    def to_dict(self) -> dict[str, Any]:
        """Преобразует runtime DTO в словарь для JSON-сериализации.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь, совпадающий по форме с `data.dialog` из API-спеки.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "public_id": self.public_id,
            "status": self.status,
            "ended_reason": self.ended_reason,
            "user_message_count": self.user_message_count,
            "assistant_message_count": self.assistant_message_count,
            "seconds_remaining": self.seconds_remaining,
            "can_send_message": self.can_send_message,
            "can_finish": self.can_finish,
            "results_url": self.results_url,
        }


class DialogRuntimeStateBuilder(BaseService[DialogRuntimeState]):
    """Строит runtime-состояние диалога по JSON-контракту API.

    Сервис инкапсулирует расчёт таймера, флагов `can_send_message`/
    `can_finish` и `results_url`, чтобы будущие runtime-endpoint-ы не
    дублировали эту логику в нескольких местах.

    Параметры:
        dialog: Объект, совместимый с `DialogStateLike`.
        now_provider: Необязательная функция текущего времени для тестов.
        results_url_builder: Необязательная функция построения URL результата.

    Возвращает:
        Экземпляр `DialogRuntimeState`.

    Исключения:
        ValueError: Возникает при отрицательных счётчиках или длительности.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(
        self,
        *,
        dialog: DialogStateLike,
        now_provider: Callable[[], datetime] | None = None,
        results_url_builder: Callable[[str], str] | None = None,
    ) -> None:
        """Сохраняет зависимости и исходный объект диалога для построения DTO.

        Параметры:
            dialog: Диалог или совместимый test-double.
            now_provider: Поставщик текущего времени для тестов.
            results_url_builder: Функция построения URL результатов.

        Возвращает:
            ``None``.

        Исключения:
            Специальные исключения не генерируются на этапе инициализации.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.dialog = dialog
        self.now_provider = now_provider or datetime.utcnow
        self.results_url_builder = results_url_builder or self._default_results_url_builder

    def execute(self) -> DialogRuntimeState:
        """Строит runtime-состояние диалога для JSON-ответа.

        Параметры:
            Явные параметры отсутствуют; используются данные конструктора.

        Возвращает:
            Экземпляр `DialogRuntimeState`.

        Исключения:
            ValueError: Возникает при невалидных числовых полях диалога.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.dialog.user_message_count < 0:
            raise ValueError("user_message_count не может быть отрицательным.")
        if self.dialog.assistant_message_count < 0:
            raise ValueError("assistant_message_count не может быть отрицательным.")
        if self.dialog.effective_duration_seconds < 0:
            raise ValueError("effective_duration_seconds не может быть отрицательным.")

        public_id = str(self.dialog.public_id)
        is_active = self.dialog.status == "active"
        seconds_remaining = self._calculate_seconds_remaining() if is_active else 0
        return DialogRuntimeState(
            public_id=public_id,
            status=str(self.dialog.status),
            ended_reason=str(self.dialog.ended_reason) if self.dialog.ended_reason else None,
            user_message_count=int(self.dialog.user_message_count),
            assistant_message_count=int(self.dialog.assistant_message_count),
            seconds_remaining=seconds_remaining,
            can_send_message=is_active,
            can_finish=is_active,
            results_url=self.results_url_builder(public_id),
        )

    def _calculate_seconds_remaining(self) -> int:
        """Вычисляет оставшееся время таймера активного диалога.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Неотрицательное число секунд до истечения таймера.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        deadline = self.dialog.started_at + timedelta(seconds=int(self.dialog.effective_duration_seconds))
        delta = int((deadline - self.now_provider()).total_seconds())
        return max(delta, 0)

    def _default_results_url_builder(self, public_id: str) -> str:
        """Строит URL результата по умолчанию без зависимости от Django reverse.

        Параметры:
            public_id: Публичный идентификатор диалога.

        Возвращает:
            Строку URL результата диалога.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"/dialogs/{public_id}/results/"
