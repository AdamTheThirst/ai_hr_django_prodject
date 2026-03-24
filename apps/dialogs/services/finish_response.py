"""Pure-Python builder успешного JSON-ответа endpoint-а ``finish``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Protocol

from apps.core.services.contracts import BaseService
from apps.dialogs.services.finish_policy import (
    RESPONSE_CODE_ANALYSIS_SKIPPED,
    RESPONSE_CODE_FINISHED,
)
from apps.dialogs.services.runtime_state import DialogRuntimeState, DialogRuntimeStateBuilder


class DialogFinishDecisionLike(Protocol):
    """Описывает минимальный контракт результата policy завершения.

    Protocol позволяет собирать успешный JSON-ответ `finish` как из
    `DialogFinishDecision`, так и из простых тестовых объектов без загрузки
    ORM и без привязки к конкретной реализации верхнего сервиса.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с кодом ответа и пользовательским сообщением.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    response_code: str
    ui_message: str


class DialogFinishResultLike(Protocol):
    """Описывает минимальный контракт результата будущего ``DialogFinishService``.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с итоговым диалогом, решением finish-policy и числом
        аналитических результатов.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    dialog_state: Any
    finish_decision: DialogFinishDecisionLike
    analysis_results_count: int


@dataclass(frozen=True, slots=True)
class DialogFinishAnalysisDTO:
    """Хранит блок ``analysis`` успешного ответа `finish`.

    DTO нужен, чтобы клиент получал компактное и стабильное состояние
    синхронного анализа без знания внутренних ORM-моделей ``AnalysisRun`` и
    ``AnalysisResult``.

    Параметры:
        status: Итоговый статус анализа в ответе клиента.
        results_count: Количество сохранённых результатов по критериям.

    Возвращает:
        Экземпляр ``DialogFinishAnalysisDTO``.

    Исключения:
        ValueError: Возникает при неподдерживаемом статусе или отрицательном
            количестве результатов.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    status: str
    results_count: int

    def __post_init__(self) -> None:
        """Проверяет допустимость статуса и счётчика аналитики.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при невалидных значениях полей DTO.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.status not in {"completed", "skipped"}:
            raise ValueError("status блока analysis должен быть completed или skipped.")
        if self.results_count < 0:
            raise ValueError("results_count не может быть отрицательным.")
        if self.status == "skipped" and self.results_count != 0:
            raise ValueError("Для status=skipped results_count должен быть равен 0.")

    def to_dict(self) -> dict[str, Any]:
        """Преобразует DTO аналитики в словарь для JSON-ответа.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь блока ``analysis``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {"status": self.status, "results_count": self.results_count}


@dataclass(frozen=True, slots=True)
class DialogFinishPayload:
    """Хранит блок ``data`` успешного ответа `finish`.

    Параметры:
        dialog: Финальное runtime-состояние диалога.
        analysis: Краткое состояние аналитики.
        redirect_url: URL экрана результатов.

    Возвращает:
        Экземпляр ``DialogFinishPayload``.

    Исключения:
        ValueError: Возникает, если ``redirect_url`` пуст.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    dialog: DialogRuntimeState
    analysis: DialogFinishAnalysisDTO
    redirect_url: str

    def __post_init__(self) -> None:
        """Проверяет обязательность ``redirect_url``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает, если URL результата пустой.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if not self.redirect_url.strip():
            raise ValueError("redirect_url не может быть пустым.")

    def to_dict(self) -> dict[str, Any]:
        """Преобразует payload в словарь блока ``data``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь финального блока ``data`` ответа `finish`.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "dialog": self.dialog.to_dict(),
            "analysis": self.analysis.to_dict(),
            "redirect_url": self.redirect_url,
        }


@dataclass(frozen=True, slots=True)
class DialogFinishResponse:
    """Хранит полный успешный JSON-ответ endpoint-а ``finish``.

    DTO объединяет response code/message и payload `data`, чтобы будущая view
    возвращала готовый сериализуемый объект без ручной сборки конверта.

    Параметры:
        ok: Признак успешного выполнения запроса.
        code: Нормализованный код ответа.
        message: Пользовательское сообщение для контролируемого финала.
        data: Полезная нагрузка успешного ответа.

    Возвращает:
        Экземпляр ``DialogFinishResponse``.

    Исключения:
        ValueError: Возникает при неподдерживаемом коде ответа или если
            ``ok`` установлен в ``False``.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    ok: bool
    code: str
    message: str
    data: DialogFinishPayload

    def __post_init__(self) -> None:
        """Проверяет согласованность успешного ответа ``finish``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при невалидных полях response-конверта.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.ok is not True:
            raise ValueError("Успешный response finish должен иметь ok=True.")
        if self.code not in {RESPONSE_CODE_FINISHED, RESPONSE_CODE_ANALYSIS_SKIPPED}:
            raise ValueError("code успешного response finish имеет неподдерживаемое значение.")

    def to_dict(self) -> dict[str, Any]:
        """Преобразует response DTO в сериализуемый словарь.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь полного успешного JSON-ответа `finish`.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "ok": self.ok,
            "code": self.code,
            "message": self.message,
            "data": self.data.to_dict(),
        }


class DialogFinishResponseBuilder(BaseService[DialogFinishResponse]):
    """Строит успешный JSON-ответ `finish` по pure-Python контракту.

    Сервис объединяет runtime-состояние диалога, решение finish-policy и
    агрегированный результат синхронного анализа в один готовый response DTO.

    Параметры:
        result: Результат будущего ``DialogFinishService`` или совместимый
            test-double.
        now_provider: Необязательный поставщик времени для runtime builder'а.
        results_url_builder: Необязательная функция построения URL результата.

    Возвращает:
        Экземпляр ``DialogFinishResponse``.

    Исключения:
        ValueError: Возникает при несогласованных данных диалога, решения или
            числа аналитических результатов.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(
        self,
        *,
        result: DialogFinishResultLike,
        now_provider: Callable[[], datetime] | None = None,
        results_url_builder: Callable[[str], str] | None = None,
    ) -> None:
        """Сохраняет зависимости и исходный результат для построения response.

        Параметры:
            result: Результат finish-сервиса или совместимый test-double.
            now_provider: Необязательный поставщик текущего времени.
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

    def execute(self) -> DialogFinishResponse:
        """Строит полный успешный response JSON для endpoint-а ``finish``.

        Параметры:
            Явные параметры отсутствуют; используются зависимости конструктора.

        Возвращает:
            Экземпляр ``DialogFinishResponse``.

        Исключения:
            ValueError: Возникает при невалидных полях диалога или анализа.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        dialog = DialogRuntimeStateBuilder(
            dialog=self.result.dialog_state,
            now_provider=self.now_provider,
            results_url_builder=self.results_url_builder,
        ).execute()
        analysis = DialogFinishAnalysisDTO(
            status=self._resolve_analysis_status(),
            results_count=int(self.result.analysis_results_count),
        )
        payload = DialogFinishPayload(
            dialog=dialog,
            analysis=analysis,
            redirect_url=dialog.results_url,
        )
        return DialogFinishResponse(
            ok=True,
            code=str(self.result.finish_decision.response_code),
            message=str(self.result.finish_decision.ui_message),
            data=payload,
        )

    def _resolve_analysis_status(self) -> str:
        """Определяет публичный статус аналитики по коду ответа ``finish``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            `completed` для завершённого анализа или `skipped` для пропуска.

        Исключения:
            ValueError: Возникает при неподдерживаемом коде ответа.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        response_code = str(self.result.finish_decision.response_code)
        if response_code == RESPONSE_CODE_FINISHED:
            return "completed"
        if response_code == RESPONSE_CODE_ANALYSIS_SKIPPED:
            return "skipped"
        raise ValueError("Неподдерживаемый response_code для успешного finish response.")
