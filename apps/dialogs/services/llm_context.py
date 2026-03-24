"""Pure-Python helpers для построения LLM-контекста диалога."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from apps.integrations.services import LLMMessage


class ScenarioPromptLike(Protocol):
    """Описывает минимальный контракт игрового промта для контекст-билдера.

    Protocol нужен, чтобы helper-функции работали как с Django ORM-моделью
    ``ScenarioPrompt``, так и с простыми тестовыми объектами без загрузки ORM.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с обязательным полем ``prompt_text``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    prompt_text: str


class GameLike(Protocol):
    """Описывает минимальный контракт игры для рендера транскрипта.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с полем ``title``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    title: str


class ScenarioLike(Protocol):
    """Описывает минимальный контракт сценария для рендера транскрипта.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с полем ``title``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    title: str


class DialogLike(Protocol):
    """Описывает минимальный контракт диалога для контекст-билдеров.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип, содержащий промт, snapshot стартовой реплики,
        статус диалога и связанные объекты игры и сценария.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    scenario_prompt_used: ScenarioPromptLike
    opening_message_snapshot_text: str
    status: str
    game: GameLike
    scenario: ScenarioLike


class DialogMessageLike(Protocol):
    """Описывает минимальный контракт сообщения диалога для helper-функций.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с ``sequence_no``, ``role`` и ``text``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    sequence_no: int
    role: str
    text: str


@dataclass(frozen=True, slots=True)
class NormalizedDialogMessage:
    """Хранит нормализованное сообщение диалога для внутренних builder'ов.

    Экземпляр используется как единый формат после сортировки и проверки
    роли/текста, чтобы обе публичные helper-функции работали с одинаковой
    чистой структурой, независимо от исходного типа объекта сообщения.

    Параметры:
        sequence_no: Порядковый номер сообщения в диалоге.
        role: Нормализованная роль ``assistant`` или ``user``.
        text: Непустой текст сообщения.

    Возвращает:
        Экземпляр ``NormalizedDialogMessage``.

    Исключения:
        ValueError: Возникает при пустом тексте или неподдерживаемой роли.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    sequence_no: int
    role: str
    text: str

    def __post_init__(self) -> None:
        """Проверяет допустимость роли и текста нормализованного сообщения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при пустом тексте, неподдерживаемой роли
                или невалидном ``sequence_no``.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if self.sequence_no < 1:
            raise ValueError("sequence_no сообщения должен быть положительным.")
        if self.role not in {"assistant", "user"}:
            raise ValueError(f"Неподдерживаемая роль сообщения диалога: {self.role}.")
        if not self.text.strip():
            raise ValueError("Текст сообщения диалога не может быть пустым.")


def build_game_call_messages(dialog: DialogLike, messages: Iterable[DialogMessageLike]) -> tuple[LLMMessage, ...]:
    """Строит нормативный массив сообщений для игрового LLM-вызова.

    Функция формирует payload по спецификации: один `system` из игрового
    промта, стартовая реплика персонажа как первое `assistant`-сообщение и
    затем весь накопленный диалог в хронологическом порядке без служебных
    записей платформы.

    Параметры:
        dialog: Диалог со snapshot стартовой реплики и использованным промтом.
        messages: Последовательность сообщений текущего диалога.

    Возвращает:
        Кортеж ``LLMMessage`` в порядке, пригодном для chat completion.

    Исключения:
        ValueError: Возникает при пустом игровом промте, пустой стартовой
            реплике или при неконсистентной истории сообщений.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    prompt_text = _require_non_empty_text(dialog.scenario_prompt_used.prompt_text, "Игровой промт")
    opening_text = _require_non_empty_text(dialog.opening_message_snapshot_text, "Стартовая реплика")
    normalized_history = _ensure_opening_message_in_history(
        opening_text=opening_text,
        messages=_normalize_dialog_messages(messages),
    )
    return (
        LLMMessage(role="system", content=prompt_text),
        *(LLMMessage(role=message.role, content=message.text) for message in normalized_history),
    )


def render_analysis_transcript(dialog: DialogLike, messages: Iterable[DialogMessageLike]) -> str:
    """Рендерит полный транскрипт диалога для аналитического LLM-вызова.

    Функция собирает единый текстовый transcript по рекомендуемому формату
    спецификации: заголовок с игрой, сценарием и статусом, затем диалог с
    явной маркировкой ролей ``ИИ`` и ``Пользователь``.

    Параметры:
        dialog: Диалог с названием игры, сценария, статусом и snapshot
            стартовой реплики.
        messages: Последовательность сообщений текущего диалога.

    Возвращает:
        Готовую строку нормализованного транскрипта.

    Исключения:
        ValueError: Возникает при пустых названиях игры/сценария,
            стартовой реплике или неконсистентной истории сообщений.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    game_title = _require_non_empty_text(dialog.game.title, "Название игры")
    scenario_title = _require_non_empty_text(dialog.scenario.title, "Название сценария")
    status = _require_non_empty_text(dialog.status, "Статус диалога")
    opening_text = _require_non_empty_text(dialog.opening_message_snapshot_text, "Стартовая реплика")
    normalized_history = _ensure_opening_message_in_history(
        opening_text=opening_text,
        messages=_normalize_dialog_messages(messages),
    )

    transcript_lines = [
        f"Игра: {game_title}",
        f"Сценарий: {scenario_title}",
        f"Статус диалога: {status}",
        "",
        "Транскрипт:",
    ]
    transcript_lines.extend(f"{_render_role_label(message.role)}: {message.text}" for message in normalized_history)
    return "\n".join(transcript_lines)


def _normalize_dialog_messages(messages: Iterable[DialogMessageLike]) -> tuple[NormalizedDialogMessage, ...]:
    """Сортирует и проверяет произвольную последовательность сообщений диалога.

    Параметры:
        messages: Исходная последовательность ORM-объектов или test-double.

    Возвращает:
        Кортеж ``NormalizedDialogMessage`` в порядке ``sequence_no``.

    Исключения:
        ValueError: Возникает при дублирующемся ``sequence_no`` или при
            невалидном сообщении.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    normalized = tuple(
        sorted(
            (
                NormalizedDialogMessage(
                    sequence_no=int(message.sequence_no),
                    role=str(message.role),
                    text=str(message.text),
                )
                for message in messages
            ),
            key=lambda item: item.sequence_no,
        )
    )
    seen_sequence_numbers: set[int] = set()
    for message in normalized:
        if message.sequence_no in seen_sequence_numbers:
            raise ValueError(f"В истории диалога обнаружен повтор sequence_no={message.sequence_no}.")
        seen_sequence_numbers.add(message.sequence_no)
    return normalized


def _ensure_opening_message_in_history(
    *,
    opening_text: str,
    messages: tuple[NormalizedDialogMessage, ...],
) -> tuple[NormalizedDialogMessage, ...]:
    """Гарантирует наличие стартовой реплики как первого assistant-сообщения.

    Если вызывающая сторона уже передала полную историю и первое сообщение
    совпадает со snapshot стартовой реплики, функция возвращает историю как
    есть. Если история начинается позднее, стартовая реплика добавляется
    синтетически. Если же первое сохранённое сообщение противоречит snapshot,
    поднимается ошибка как признак повреждённой истории.

    Параметры:
        opening_text: Зафиксированная стартовая реплика персонажа.
        messages: Уже отсортированная и нормализованная история сообщений.

    Возвращает:
        Кортеж ``NormalizedDialogMessage`` с гарантированным opening message.

    Исключения:
        ValueError: Возникает при противоречии между snapshot и первым
            сохранённым сообщением.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    if not messages:
        return (NormalizedDialogMessage(sequence_no=1, role="assistant", text=opening_text),)

    first_message = messages[0]
    if first_message.sequence_no == 1:
        if first_message.role != "assistant":
            raise ValueError("Первое сообщение диалога с sequence_no=1 должно иметь роль assistant.")
        if first_message.text.strip() != opening_text.strip():
            raise ValueError("Первое сообщение диалога не совпадает со snapshot стартовой реплики.")
        return messages

    synthetic_opening = NormalizedDialogMessage(sequence_no=1, role="assistant", text=opening_text)
    return (synthetic_opening, *messages)


def _render_role_label(role: str) -> str:
    """Преобразует техническую роль сообщения в человекочитаемую подпись.

    Параметры:
        role: Технический код роли ``assistant`` или ``user``.

    Возвращает:
        Русскую подпись для аналитического транскрипта.

    Исключения:
        ValueError: Возникает при неизвестной роли.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    if role == "assistant":
        return "ИИ"
    if role == "user":
        return "Пользователь"
    raise ValueError(f"Неизвестная роль сообщения для рендера транскрипта: {role}.")


def _require_non_empty_text(value: Any, field_label: str) -> str:
    """Проверяет, что строковое поле не пустое и не состоит из пробелов.

    Параметры:
        value: Исходное значение поля.
        field_label: Человекочитаемое название поля для текста ошибки.

    Возвращает:
        Очищенную от краевых пробелов строку.

    Исключения:
        ValueError: Возникает при пустом значении.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_label} не может быть пустым.")
    return normalized
