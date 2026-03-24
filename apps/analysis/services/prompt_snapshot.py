"""Pure-Python builder snapshot-полей результата аналитики."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from apps.core.services.contracts import BaseService


class AnalysisPromptLike(Protocol):
    """Описывает минимальный контракт аналитического промта для snapshot-builder.

    Protocol позволяет строить snapshot как из ORM-модели `AnalysisPrompt`,
    так и из тестовых объектов без обязательной загрузки Django ORM.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с полями, которые должны попасть в `AnalysisResult`.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    sort_order: int
    alias: str
    title: str
    header_text: str
    comment_text: str
    min_rating: int
    max_rating: int


@dataclass(frozen=True, slots=True)
class AnalysisPromptSnapshot:
    """Хранит snapshot-поля аналитического промта для `AnalysisResult`.

    DTO нужен, чтобы будущий `AnalysisService` копировал в результат только
    согласованные snapshot-значения, не завися от последующих изменений
    `AnalysisPrompt` в админке.

    Параметры:
        sort_order_snapshot: Порядок показа критерия на момент запуска.
        alias_snapshot: Alias критерия на момент запуска.
        title_snapshot: Название критерия на момент запуска.
        header_snapshot_text: Заголовок карточки результата.
        comment_snapshot_text: Административный комментарий/подсказка.
        rating_min: Минимальный балл шкалы.
        rating_max: Максимальный балл шкалы.

    Возвращает:
        Экземпляр `AnalysisPromptSnapshot`.

    Исключения:
        ValueError: Возникает при пустых обязательных строках или
            некорректном диапазоне рейтинга.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    sort_order_snapshot: int
    alias_snapshot: str
    title_snapshot: str
    header_snapshot_text: str
    comment_snapshot_text: str
    rating_min: int
    rating_max: int

    def __post_init__(self) -> None:
        """Проверяет корректность snapshot-полей аналитического критерия.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при пустых строках, отрицательном порядке
                показа или несовместимых границах рейтинга.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.sort_order_snapshot < 0:
            raise ValueError("sort_order_snapshot не может быть отрицательным.")
        if not self.alias_snapshot.strip():
            raise ValueError("alias_snapshot не может быть пустым.")
        if not self.title_snapshot.strip():
            raise ValueError("title_snapshot не может быть пустым.")
        if not self.header_snapshot_text.strip():
            raise ValueError("header_snapshot_text не может быть пустым.")
        if self.rating_min > self.rating_max:
            raise ValueError("rating_min не может быть больше rating_max.")

    def to_result_fields(self) -> dict[str, Any]:
        """Преобразует snapshot в словарь полей для `AnalysisResult`.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь с именами полей `AnalysisResult`.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "sort_order_snapshot": self.sort_order_snapshot,
            "alias_snapshot": self.alias_snapshot,
            "title_snapshot": self.title_snapshot,
            "header_snapshot_text": self.header_snapshot_text,
            "comment_snapshot_text": self.comment_snapshot_text,
            "rating_min": self.rating_min,
            "rating_max": self.rating_max,
        }


class AnalysisPromptSnapshotBuilder(BaseService[AnalysisPromptSnapshot]):
    """Строит snapshot-поля `AnalysisResult` из активного `AnalysisPrompt`.

    Сервис инкапсулирует копирование согласованных полей критерия анализа в
    отдельный DTO, чтобы будущий `AnalysisService` не размазывал эту логику
    по нескольким местам и не зависел от живого объекта промта после старта.

    Параметры:
        analysis_prompt: Объект, совместимый с `AnalysisPromptLike`.

    Возвращает:
        Экземпляр `AnalysisPromptSnapshot`.

    Исключения:
        ValueError: Возникает при пустых обязательных полях или некорректном
            диапазоне рейтинга.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def __init__(self, *, analysis_prompt: AnalysisPromptLike) -> None:
        """Сохраняет источник snapshot-полей для будущего построения DTO.

        Параметры:
            analysis_prompt: Аналитический промт или совместимый test-double.

        Возвращает:
            ``None``.

        Исключения:
            Специальные исключения не генерируются на этапе инициализации.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.analysis_prompt = analysis_prompt

    def execute(self) -> AnalysisPromptSnapshot:
        """Строит snapshot DTO из полей текущего аналитического промта.

        Параметры:
            Явные параметры отсутствуют; используется объект конструктора.

        Возвращает:
            Экземпляр `AnalysisPromptSnapshot`.

        Исключения:
            ValueError: Возникает, если snapshot-поля не проходят базовую
                валидацию.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return AnalysisPromptSnapshot(
            sort_order_snapshot=int(self.analysis_prompt.sort_order),
            alias_snapshot=str(self.analysis_prompt.alias),
            title_snapshot=str(self.analysis_prompt.title),
            header_snapshot_text=str(self.analysis_prompt.header_text),
            comment_snapshot_text=str(self.analysis_prompt.comment_text or ""),
            rating_min=int(self.analysis_prompt.min_rating),
            rating_max=int(self.analysis_prompt.max_rating),
        )
