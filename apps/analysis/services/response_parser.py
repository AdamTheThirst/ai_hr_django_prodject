"""Парсер и валидатор JSON-ответа аналитической LLM."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from apps.core.services.contracts import BaseService


VALIDATION_STATUS_VALID = "valid"
VALIDATION_STATUS_INVALID_JSON = "invalid_json"
VALIDATION_STATUS_INVALID_SCHEMA = "invalid_schema"


@dataclass(frozen=True, slots=True)
class ParsedAnalysisResponse:
    """Хранит валидный минимальный payload аналитического ответа.

    DTO используется после успешного разбора JSON-ответа LLM и содержит
    только поля минимального контракта, которые действительно разрешены к
    сохранению в ``AnalysisResult`` и ``parsed_json_snapshot``.

    Параметры:
        rating: Целочисленный балл по критерию.
        text: Непустой текст разбора.

    Возвращает:
        Экземпляр ``ParsedAnalysisResponse``.

    Исключения:
        ValueError: Возникает, если ``text`` пустой.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    rating: int
    text: str

    def __post_init__(self) -> None:
        """Проверяет непустоту итогового текста разбора.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает, если ``text`` пустой после ``strip()``.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if not self.text.strip():
            raise ValueError("Текст аналитического ответа не может быть пустым.")

    def to_parsed_json_snapshot(self) -> dict[str, Any]:
        """Преобразует DTO в JSON-снимок для сохранения в ``AnalysisResult``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь минимального контракта ``{rating, text}``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {"rating": self.rating, "text": self.text}


@dataclass(frozen=True, slots=True)
class AnalysisResponseParserResult:
    """Описывает результат разбора одного аналитического ответа модели.

    Экземпляр хранит как успешный нормализованный результат, так и признаки
    неуспеха: код/статус валидации и диагностическое сообщение. Это позволяет
    будущему ``analysis``-сервису единообразно заполнять ``AnalysisResult`` и
    решать, нужна ли повторная попытка или fallback.

    Параметры:
        validation_status: Статус разбора ``valid``/``invalid_json``/
            ``invalid_schema``.
        parsed_response: Валидный минимальный payload при успехе.
        normalized_payload: Внутренняя нормализованная структура с ``meta``.
        error_code: Доменный код ошибки при неуспехе.
        error_message: Человекочитаемая причина неуспеха.
        raw_response_text: Исходный текст ответа LLM.

    Возвращает:
        Экземпляр ``AnalysisResponseParserResult``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    validation_status: str
    parsed_response: ParsedAnalysisResponse | None
    normalized_payload: dict[str, Any] | None
    error_code: str | None
    error_message: str
    raw_response_text: str

    @property
    def is_valid(self) -> bool:
        """Возвращает признак успешного прохождения валидации.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``True`` только для статуса ``valid``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return self.validation_status == VALIDATION_STATUS_VALID


class AnalysisResponseParser(BaseService[AnalysisResponseParserResult]):
    """Валидирует и нормализует один JSON-ответ аналитической модели.

    Сервис реализует контракт из спецификации для ``AnalysisResponseParser``:
    принимает сырой текст ответа LLM, проверяет JSON-синтаксис, наличие полей
    ``rating`` и ``text``, типы значений и диапазон рейтинга, после чего
    возвращает единый объект результата без зависимости от ORM.

    Параметры:
        raw_response_text: Исходный текст ответа аналитической LLM.
        rating_min: Минимально допустимое значение рейтинга.
        rating_max: Максимально допустимое значение рейтинга.
        attempt_count: Номер попытки LLM для заполнения meta-поля.

    Возвращает:
        Экземпляр ``AnalysisResponseParserResult``.

    Исключения:
        ValueError: Возникает при некорректной конфигурации самого парсера,
            например если ``rating_min > rating_max`` или ``attempt_count < 1``.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(
        self,
        *,
        raw_response_text: str,
        rating_min: int,
        rating_max: int,
        attempt_count: int = 1,
    ) -> None:
        """Сохраняет входные данные для последующего выполнения парсинга.

        Параметры:
            raw_response_text: Сырой текст ответа аналитической LLM.
            rating_min: Минимум шкалы критерия.
            rating_max: Максимум шкалы критерия.
            attempt_count: Порядковый номер попытки LLM.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает, если диапазон рейтинга некорректен или
                ``attempt_count`` меньше единицы.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if rating_min > rating_max:
            raise ValueError("rating_min не может быть больше rating_max.")
        if attempt_count < 1:
            raise ValueError("attempt_count должен быть положительным числом.")

        self.raw_response_text = raw_response_text
        self.rating_min = rating_min
        self.rating_max = rating_max
        self.attempt_count = attempt_count

    def execute(self) -> AnalysisResponseParserResult:
        """Разбирает и валидирует ответ аналитической модели.

        Параметры:
            Явные параметры отсутствуют; используются данные конструктора.

        Возвращает:
            ``AnalysisResponseParserResult`` со статусом валидации и при
            успехе — с нормализованным payload.

        Исключения:
            Специальные исключения не генерируются: ошибки контракта
                возвращаются в виде результата со статусом неуспеха.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        try:
            decoded = json.loads(self.raw_response_text)
        except json.JSONDecodeError as exc:
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_JSON,
                error_message=f"Ответ аналитической LLM не является валидным JSON: {exc.msg}.",
            )

        if not isinstance(decoded, dict):
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_SCHEMA,
                error_message="JSON аналитического ответа должен быть объектом верхнего уровня.",
            )
        if "rating" not in decoded:
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_SCHEMA,
                error_message="В JSON аналитического ответа отсутствует обязательное поле rating.",
            )
        if "text" not in decoded:
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_SCHEMA,
                error_message="В JSON аналитического ответа отсутствует обязательное поле text.",
            )

        rating = decoded["rating"]
        text = decoded["text"]
        if isinstance(rating, bool) or not isinstance(rating, int):
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_SCHEMA,
                error_message="Поле rating должно быть целым числом.",
            )
        if not isinstance(text, str) or not text.strip():
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_SCHEMA,
                error_message="Поле text должно быть непустой строкой.",
            )
        if not self.rating_min <= rating <= self.rating_max:
            return self._build_error_result(
                validation_status=VALIDATION_STATUS_INVALID_SCHEMA,
                error_message=(
                    f"Поле rating должно лежать в диапазоне [{self.rating_min}, {self.rating_max}]."
                ),
            )

        parsed_response = ParsedAnalysisResponse(rating=rating, text=text.strip())
        normalized_payload = {
            **parsed_response.to_parsed_json_snapshot(),
            "meta": {
                "validation_status": VALIDATION_STATUS_VALID,
                "attempt_count": self.attempt_count,
            },
        }
        return AnalysisResponseParserResult(
            validation_status=VALIDATION_STATUS_VALID,
            parsed_response=parsed_response,
            normalized_payload=normalized_payload,
            error_code=None,
            error_message="",
            raw_response_text=self.raw_response_text,
        )

    def _build_error_result(self, *, validation_status: str, error_message: str) -> AnalysisResponseParserResult:
        """Создаёт единый объект ошибки разбора аналитического ответа.

        Параметры:
            validation_status: Статус ``invalid_json`` или ``invalid_schema``.
            error_message: Диагностическое объяснение причины неуспеха.

        Возвращает:
            ``AnalysisResponseParserResult`` без ``parsed_response``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return AnalysisResponseParserResult(
            validation_status=validation_status,
            parsed_response=None,
            normalized_payload=None,
            error_code=validation_status,
            error_message=error_message,
            raw_response_text=self.raw_response_text,
        )
