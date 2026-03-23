"""Pure-Python builder payload ответа ``send-message`` для диалогов."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Protocol

from apps.core.services.contracts import BaseService
from apps.dialogs.services.message_dto import DialogMessageDTO, DialogMessageDTOBuilder
from apps.dialogs.services.runtime_state import DialogRuntimeState, DialogRuntimeStateBuilder


class DialogSendMessagePayloadLike(Protocol):
    """Описывает минимальный контракт результата ``DialogMessageService``.

    Protocol позволяет собрать JSON payload ответа `send-message` как из
    будущего ORM- и сервисного результата, так и из простого test-double без
    загрузки Django ORM.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с диалогом и двумя сообщениями ответа.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    dialog_state: Any
    user_message: Any
    assistant_message: Any


@dataclass(frozen=True, slots=True)
class DialogSendMessagePayload:
    """Хранит payload блока ``data`` для успешного ответа `send-message`.

    DTO соответствует контракту `POST /dialogs/<dialog_public_id>/send-message/`
    из API-спеки и нужен, чтобы endpoint-слой не собирал вложенные словари
    вручную в view или контроллере.

    Параметры:
        dialog: Runtime-состояние диалога после обработки сообщения.
        user_message: DTO сохранённой пользовательской реплики.
        assistant_message: DTO сохранённого ответа персонажа.

    Возвращает:
        Экземпляр ``DialogSendMessagePayload``.

    Исключения:
        ValueError: Возникает, если роли сообщений не соответствуют контракту
            `user_message` / `assistant_message`.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    dialog: DialogRuntimeState
    user_message: DialogMessageDTO
    assistant_message: DialogMessageDTO

    def __post_init__(self) -> None:
        """Проверяет согласованность ролей вложенных DTO сообщений.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает, если `user_message` не имеет роль `user`
                или `assistant_message` не имеет роль `assistant`.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.user_message.role != "user":
            raise ValueError("user_message должен иметь роль user.")
        if self.assistant_message.role != "assistant":
            raise ValueError("assistant_message должен иметь роль assistant.")

    def to_dict(self) -> dict[str, Any]:
        """Преобразует payload в словарь для JSON-ответа endpoint-а.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь блока ``data`` из успешного ответа `send-message`.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "dialog": self.dialog.to_dict(),
            "user_message": self.user_message.to_dict(),
            "assistant_message": self.assistant_message.to_dict(),
        }


class DialogSendMessagePayloadBuilder(BaseService[DialogSendMessagePayload]):
    """Строит payload успешного ответа ``send-message``.

    Сервис использует уже существующие builder'ы runtime-состояния диалога и
    DTO сообщений, чтобы endpoint возвращал единый контракт API без
    дублирования вложенной сериализации.

    Параметры:
        result: Результат работы будущего ``DialogMessageService`` или
            совместимый test-double.

    Возвращает:
        Экземпляр ``DialogSendMessagePayload``.

    Исключения:
        ValueError: Возникает при несогласованных ролях сообщений или при
            невалидных полях вложенных DTO.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(
        self,
        *,
        result: DialogSendMessagePayloadLike,
        now_provider: Callable[[], datetime] | None = None,
        results_url_builder: Callable[[str], str] | None = None,
    ) -> None:
        """Сохраняет зависимости и исходный результат для построения payload.

        Параметры:
            result: Результат message-сервиса или совместимый test-double.
            now_provider: Необязательный поставщик текущего времени для
                детерминированных тестов runtime-состояния.
            results_url_builder: Необязательная функция построения URL
                страницы результатов.

        Возвращает:
            ``None``.

        Исключения:
            Специальные исключения не генерируются на этапе инициализации.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.result = result
        self.now_provider = now_provider
        self.results_url_builder = results_url_builder

    def execute(self) -> DialogSendMessagePayload:
        """Строит payload блока ``data`` успешного ответа ``send-message``.

        Параметры:
            Явные параметры отсутствуют; используются зависимости конструктора.

        Возвращает:
            Экземпляр ``DialogSendMessagePayload``.

        Исключения:
            ValueError: Возникает при невалидных полях диалога или сообщений.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return DialogSendMessagePayload(
            dialog=DialogRuntimeStateBuilder(
                dialog=self.result.dialog_state,
                now_provider=self.now_provider,
                results_url_builder=self.results_url_builder,
            ).execute(),
            user_message=DialogMessageDTOBuilder(message=self.result.user_message).execute(),
            assistant_message=DialogMessageDTOBuilder(message=self.result.assistant_message).execute(),
        )
