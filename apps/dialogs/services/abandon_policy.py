"""Pure-Python policy для покидания страницы активного диалога."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.services.contracts import BaseService


ABANDON_REASON_PAGE_LEAVE = "page_leave"
ABANDON_REASON_INACTIVE_TIMEOUT = "inactive_timeout"
DIALOG_STATUS_ABORTED = "aborted"
ANALYSIS_STATE_START = "start"
ANALYSIS_STATE_SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class DialogAbandonDecision:
    """Хранит итоговое решение по покиданию страницы диалога.

    DTO фиксирует минимальный runtime-результат, который нужен будущему
    `DialogAbandonService`: какой статус должен получить диалог, какая
    причина завершения должна быть записана и следует ли запускать анализ.

    Параметры:
        dialog_status: Итоговый статус диалога после abandon-сценария.
        ended_reason: Причина завершения `page_leave` или `inactive_timeout`.
        analysis_state: Решение для аналитики: `start` или `skipped`.
        analysis_was_started: Булев признак необходимости запуска анализа.

    Возвращает:
        Экземпляр ``DialogAbandonDecision``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    dialog_status: str
    ended_reason: str
    analysis_state: str
    analysis_was_started: bool


class DialogAbandonDecisionService(BaseService[DialogAbandonDecision]):
    """Определяет, что делать при покидании пользователем страницы диалога.

    Сервис покрывает чистую продуктовую логику abandon-сценария: диалог
    всегда переводится в `aborted`, а анализ запускается только если у
    пользователя уже была хотя бы одна реплика. Это соответствует правилам
    `DialogAbandonService` и описанным статусам в `DATA_MODELS.md`.

    Параметры:
        reason: Причина abandon-сценария: `page_leave` или
            `inactive_timeout`.
        user_message_count: Количество пользовательских реплик в диалоге.

    Возвращает:
        Экземпляр ``DialogAbandonDecision``.

    Исключения:
        ValueError: Возникает при неподдерживаемой причине завершения или
            отрицательном количестве пользовательских реплик.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(self, *, reason: str, user_message_count: int) -> None:
        """Сохраняет входные параметры abandon-решения.

        Параметры:
            reason: Причина сценария покидания страницы.
            user_message_count: Количество сообщений пользователя.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при невалидных аргументах.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if reason not in {ABANDON_REASON_PAGE_LEAVE, ABANDON_REASON_INACTIVE_TIMEOUT}:
            raise ValueError("reason должен быть page_leave или inactive_timeout.")
        if user_message_count < 0:
            raise ValueError("user_message_count не может быть отрицательным.")
        self.reason = reason
        self.user_message_count = user_message_count

    def execute(self) -> DialogAbandonDecision:
        """Вычисляет согласованное abandon-решение для runtime-слоя.

        Параметры:
            Явные параметры отсутствуют; используются данные конструктора.

        Возвращает:
            ``DialogAbandonDecision`` с итоговым статусом и решением по анализу.

        Исключения:
            Специальные исключения не генерируются: ошибки входа уже
                проверены в конструкторе.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return DialogAbandonDecision(
            dialog_status=DIALOG_STATUS_ABORTED,
            ended_reason=self.reason,
            analysis_state=ANALYSIS_STATE_START if self.user_message_count > 0 else ANALYSIS_STATE_SKIPPED,
            analysis_was_started=self.user_message_count > 0,
        )
