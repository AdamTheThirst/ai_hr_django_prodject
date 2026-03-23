"""Pure-Python policy для завершения диалога и решения о запуске анализа."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.services.contracts import BaseService


FINISH_REASON_MANUAL_FEEDBACK = "manual_feedback"
FINISH_REASON_TIMEOUT = "timeout"
DIALOG_STATUS_FINISHED = "finished"
DIALOG_STATUS_ANALYSIS_SKIPPED = "analysis_skipped"
ANALYSIS_STATE_START = "start"
ANALYSIS_STATE_SKIPPED = "skipped"
RESPONSE_CODE_FINISHED = "finished"
RESPONSE_CODE_ANALYSIS_SKIPPED = "analysis_skipped_no_user_messages"
NO_USER_MESSAGES_REASON = "no_user_messages"
ANALYSIS_SKIPPED_MESSAGE = "Анализ не выполнялся, потому что пользователь не отправил ни одной реплики."


@dataclass(frozen=True, slots=True)
class DialogFinishDecision:
    """Хранит итоговое решение сервиса завершения диалога.

    DTO нужен как промежуточный runtime-результат между endpoint-слоем и
    будущим ORM-backed `DialogFinishService`. Он фиксирует финальный статус
    диалога, причину завершения, необходимость запуска анализа и код ответа,
    не смешивая это с HTTP-деталями и сохранением в БД.

    Параметры:
        dialog_status: Итоговый статус диалога.
        ended_reason: Итоговая причина завершения.
        analysis_state: Решение для аналитики: запускать или пропустить.
        analysis_was_started: Булев признак фактической необходимости старта.
        response_code: Нормализованный код runtime-ответа.
        ui_message: Пользовательское сообщение для контролируемого финала.

    Возвращает:
        Экземпляр ``DialogFinishDecision``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    dialog_status: str
    ended_reason: str
    analysis_state: str
    analysis_was_started: bool
    response_code: str
    ui_message: str


class DialogFinishDecisionService(BaseService[DialogFinishDecision]):
    """Определяет итог завершения активного диалога по pure-Python правилам.

    Сервис реализует самую узкую и стабильную часть `DialogFinishService`:
    по причине завершения и числу пользовательских реплик он выбирает финальный
    статус диалога, согласованную причину завершения и факт запуска анализа.

    Параметры:
        reason: Причина завершения из допустимого набора `manual_feedback`
            или `timeout`.
        user_message_count: Количество реплик пользователя в диалоге.

    Возвращает:
        Экземпляр ``DialogFinishDecision``.

    Исключения:
        ValueError: Возникает при неподдерживаемой причине завершения или
            отрицательном количестве пользовательских реплик.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(self, *, reason: str, user_message_count: int) -> None:
        """Сохраняет входные данные для последующего расчёта решения.

        Параметры:
            reason: Причина завершения диалога.
            user_message_count: Количество пользовательских реплик.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при невалидных аргументах.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if reason not in {FINISH_REASON_MANUAL_FEEDBACK, FINISH_REASON_TIMEOUT}:
            raise ValueError("reason должен быть manual_feedback или timeout.")
        if user_message_count < 0:
            raise ValueError("user_message_count не может быть отрицательным.")
        self.reason = reason
        self.user_message_count = user_message_count

    def execute(self) -> DialogFinishDecision:
        """Вычисляет согласованное решение по завершению диалога.

        Параметры:
            Явные параметры отсутствуют; используются данные конструктора.

        Возвращает:
            ``DialogFinishDecision`` с готовым решением для runtime-слоя.

        Исключения:
            Специальные исключения не генерируются: ошибки входа уже
                отлавливаются в конструкторе.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.user_message_count > 0:
            return DialogFinishDecision(
                dialog_status=DIALOG_STATUS_FINISHED,
                ended_reason=self.reason,
                analysis_state=ANALYSIS_STATE_START,
                analysis_was_started=True,
                response_code=RESPONSE_CODE_FINISHED,
                ui_message="",
            )

        return DialogFinishDecision(
            dialog_status=DIALOG_STATUS_ANALYSIS_SKIPPED,
            ended_reason=NO_USER_MESSAGES_REASON,
            analysis_state=ANALYSIS_STATE_SKIPPED,
            analysis_was_started=False,
            response_code=RESPONSE_CODE_ANALYSIS_SKIPPED,
            ui_message=ANALYSIS_SKIPPED_MESSAGE,
        )
