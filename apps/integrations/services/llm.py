"""OpenAI-compatible интеграция для игровых и аналитических вызовов LLM."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Protocol

if TYPE_CHECKING:
    from apps.platform_config.models import PlatformSettings


class PlatformSettingsLike(Protocol):
    """Описывает минимальный набор полей настроек, нужных LLM-слою.

    Protocol нужен, чтобы интеграционный слой можно было тестировать без
    обязательной загрузки Django ORM в среде unit-тестов. При реальном
    выполнении этим контрактом обычно выступает модель ``PlatformSettings``.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Структурный тип с ожидаемыми LLM-полями настроек.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    llm_base_url: str
    llm_api_key: str
    llm_model_name: str
    llm_temperature: Any
    llm_top_p: Any
    llm_game_max_tokens: int
    llm_analysis_max_tokens: int
    max_user_message_chars: int
    max_game_reply_chars: int
    max_analysis_reply_chars: int


class LLMMode(str, Enum):
    """Перечисляет поддерживаемые режимы вызова LLM.

    Перечисление используется сервисным слоем, чтобы явно разделять игровые,
    аналитические и служебные вызовы при использовании одного и того же
    OpenAI-compatible backend. Разделение нужно для выбора корректного лимита
    ``max_tokens`` и для будущего технического логирования.

    Параметры:
        Явные параметры не принимаются.

    Возвращает:
        Строковые коды режимов ``game``, ``analysis`` и ``system``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    GAME = "game"
    ANALYSIS = "analysis"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class LLMMessage:
    """Описывает одно сообщение в OpenAI-compatible chat completion.

    Экземпляры этого класса используются при построении игрового и
    аналитического контекста перед вызовом внешней модели. Поле ``role``
    намеренно оставлено строковым, потому что поддерживаемый контракт
    спецификации ограничивается ролями ``system``, ``assistant`` и ``user``.

    Параметры:
        role: Роль сообщения в chat completion payload.
        content: Текстовое содержимое сообщения.

    Возвращает:
        Экземпляр ``LLMMessage``.

    Исключения:
        ValueError: Возникает, если роль не поддерживается или текст пустой.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    role: str
    content: str

    def __post_init__(self) -> None:
        """Проверяет корректность роли и содержимого сообщения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает, если роль не входит в нормативный набор
                или если ``content`` пустой после ``strip()``.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        allowed_roles = {"system", "assistant", "user"}
        if self.role not in allowed_roles:
            raise ValueError(f"Неподдерживаемая роль сообщения: {self.role}.")
        if not self.content.strip():
            raise ValueError("Сообщение для LLM не может быть пустым.")

    def to_payload(self) -> dict[str, str]:
        """Преобразует сообщение в формат SDK OpenAI-compatible клиента.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь вида ``{'role': ..., 'content': ...}``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Описывает унифицированный вход для OpenAI-compatible вызова.

    DTO служит стабильным внутренним контрактом между прикладными сервисами
    и интеграционным слоем. Он позволяет не тащить детали конкретного SDK в
    приложения ``dialogs`` и ``analysis``.

    Параметры:
        mode: Режим вызова LLM.
        base_url: Базовый URL OpenAI-compatible/vLLM сервера.
        api_key: Ключ доступа к серверу. Может быть пустой строкой.
        model_name: Имя модели для chat completion.
        temperature: Температура генерации.
        top_p: Параметр nucleus sampling.
        max_tokens: Лимит генерируемых токенов.
        messages: Нормализованный массив сообщений chat completion.

    Возвращает:
        Экземпляр ``LLMRequest``.

    Исключения:
        ValueError: Возникает при пустом URL, имени модели, невалидных
            числовых параметрах или пустом списке сообщений.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    mode: LLMMode
    base_url: str
    api_key: str
    model_name: str
    temperature: float
    top_p: float
    max_tokens: int
    messages: tuple[LLMMessage, ...]

    def __post_init__(self) -> None:
        """Проверяет согласованность параметров запроса к модели.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает при нарушении базовых диапазонов и если
                список сообщений пуст.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if not self.base_url.strip():
            raise ValueError("Для запроса LLM требуется непустой base_url.")
        if not self.model_name.strip():
            raise ValueError("Для запроса LLM требуется имя модели.")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature должна быть в диапазоне от 0 до 2.")
        if not 0 <= self.top_p <= 1:
            raise ValueError("top_p должен быть в диапазоне от 0 до 1.")
        if self.max_tokens < 1:
            raise ValueError("max_tokens должен быть положительным числом.")
        if not self.messages:
            raise ValueError("Запрос LLM должен содержать хотя бы одно сообщение.")

    def to_payload(self) -> dict[str, Any]:
        """Собирает payload для метода ``chat.completions.create``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Словарь с параметрами, совместимыми с OpenAI-compatible SDK.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return {
            "model": self.model_name,
            "messages": [message.to_payload() for message in self.messages],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Описывает нормализованный ответ интеграционного слоя LLM.

    Экземпляр возвращается прикладным сервисам вместо сырого ответа SDK,
    чтобы верхние слои опирались на стабильные поля, а не на структуру
    сторонней библиотеки.

    Параметры:
        reply_text: Текст готового ответа модели.
        provider_request_id: Идентификатор провайдера, если он доступен.
        raw_provider_payload: Упрощённый безопасный снимок ответа провайдера.

    Возвращает:
        Экземпляр ``LLMResponse``.

    Исключения:
        ValueError: Возникает, если ``reply_text`` пустой.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    reply_text: str
    provider_request_id: str
    raw_provider_payload: dict[str, Any]

    def __post_init__(self) -> None:
        """Проверяет, что интеграционный слой вернул непустой текст.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValueError: Возникает, если ``reply_text`` пустой.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        if not self.reply_text.strip():
            raise ValueError("LLMResponse должен содержать непустой reply_text.")


class LLMIntegrationError(Exception):
    """Базовое исключение интеграционного слоя LLM.

    Исключение используется как общий корень для нормализованных ошибок,
    которые прикладной слой может безопасно перехватывать без знания деталей
    конкретного SDK или транспортного стека.

    Параметры:
        message: Текст человекочитаемого описания ошибки.

    Возвращает:
        Экземпляр исключения ``LLMIntegrationError``.

    Исключения:
        Специальные дополнительные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """


class LLMConfigurationError(LLMIntegrationError):
    """Сигнализирует о некорректной конфигурации LLM.

    Исключение поднимается, когда отсутствуют активные настройки платформы
    либо в них не хватает обязательных значений для инициализации клиента.

    Параметры:
        Наследует параметры базового ``Exception``.

    Возвращает:
        Экземпляр исключения ``LLMConfigurationError``.

    Исключения:
        Специальные дополнительные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """


class LLMTemporaryError(LLMIntegrationError):
    """Описывает временную внешнюю ошибку при обращении к LLM.

    Исключение предназначено для случаев сетевой недоступности, таймаута,
    внутренних 5xx-ошибок провайдера и других ситуаций, где допустима
    стратегия повторной попытки на уровне прикладных сервисов.

    Параметры:
        Наследует параметры базового ``Exception``.

    Возвращает:
        Экземпляр исключения ``LLMTemporaryError``.

    Исключения:
        Специальные дополнительные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """


class LLMEmptyResponseError(LLMIntegrationError):
    """Сигнализирует, что провайдер вернул пустой или нечитаемый ответ.

    Случай выделен в отдельный тип, потому что верхний уровень может считать
    его интеграционной ошибкой без повторного разбора структуры ответа SDK.

    Параметры:
        Наследует параметры базового ``Exception``.

    Возвращает:
        Экземпляр исключения ``LLMEmptyResponseError``.

    Исключения:
        Специальные дополнительные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """


@dataclass(frozen=True, slots=True)
class PlatformLLMSettingsSnapshot:
    """Хранит снимок LLM-настроек платформы для конкретного режима.

    DTO собирается из активной записи ``PlatformSettings`` и нужен для
    последующего старта диалога, анализа и вызовов системных промтов без
    прямой зависимости доменных сервисов от ORM-модели настроек.

    Параметры:
        base_url: Базовый URL OpenAI-compatible/vLLM сервера.
        api_key: Ключ доступа.
        model_name: Имя модели по умолчанию.
        temperature: Температура генерации.
        top_p: Параметр nucleus sampling.
        max_tokens: Режимно-зависимый лимит генерации.
        max_user_message_chars: Серверный лимит пользовательского сообщения.
        max_game_reply_chars: Лимит длины игрового ответа.
        max_analysis_reply_chars: Лимит длины аналитического ответа.

    Возвращает:
        Экземпляр ``PlatformLLMSettingsSnapshot``.

    Исключения:
        Специальные исключения не генерируются.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    base_url: str
    api_key: str
    model_name: str
    temperature: float
    top_p: float
    max_tokens: int
    max_user_message_chars: int
    max_game_reply_chars: int
    max_analysis_reply_chars: int


class OpenAICompatibleLLMClient:
    """Инкапсулирует вызовы OpenAI-compatible/vLLM chat completion API.

    Класс является единственной точкой обращения к внешнему SDK внутри
    приложения ``integrations``. Он принимает нормализованный ``LLMRequest``,
    формирует запрос в OpenAI-compatible формате и возвращает безопасный
    ``LLMResponse`` для сервисного слоя.

    Параметры:
        client_factory: Фабрика, создающая конкретный экземпляр SDK-клиента.
            Если не передана, клиент будет создан через импорт ``openai``.

    Возвращает:
        Экземпляр ``OpenAICompatibleLLMClient``.

    Исключения:
        LLMConfigurationError: Возможна при отсутствии библиотеки ``openai``.

    Побочные эффекты:
        При выполнении запроса обращается к внешнему LLM-серверу.
    """

    def __init__(self, client_factory: Callable[..., Any] | None = None) -> None:
        """Сохраняет фабрику SDK-клиента для последующих вызовов.

        Параметры:
            client_factory: Опциональная фабрика OpenAI-compatible клиента.

        Возвращает:
            ``None``.

        Исключения:
            Специальные исключения не генерируются на этапе инициализации.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.client_factory = client_factory or self._build_default_client_factory()

    def _build_default_client_factory(self) -> Callable[..., Any]:
        """Ленивая загрузка класса ``OpenAI`` из сторонней библиотеки.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Вызываемый объект, совместимый с конструктором ``OpenAI``.

        Исключения:
            LLMConfigurationError: Возникает, если библиотека ``openai`` не
                установлена в окружении.

        Побочные эффекты:
            Выполняет импорт сторонней зависимости во время инициализации.
        """
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                "Библиотека 'openai' не установлена. Установите зависимость для работы с vLLM."
            ) from exc
        return OpenAI

    def generate_reply(self, request: LLMRequest) -> LLMResponse:
        """Выполняет chat completion и нормализует ответ провайдера.

        Параметры:
            request: Нормализованный запрос к OpenAI-compatible backend.

        Возвращает:
            Экземпляр ``LLMResponse`` с текстом ответа и безопасным снимком
            полезных полей провайдера.

        Исключения:
            LLMEmptyResponseError: Возникает, если ответ не содержит текста.
            LLMTemporaryError: Возникает при внешней ошибке SDK или сети.

        Побочные эффекты:
            Инициирует сетевой запрос к LLM-провайдеру.
        """
        client = self.client_factory(base_url=request.base_url, api_key=request.api_key)
        try:
            response = client.chat.completions.create(**request.to_payload())
        except Exception as exc:  # pragma: no cover - ветка защищает внешнюю зависимость.
            raise LLMTemporaryError(f"Ошибка OpenAI-compatible вызова LLM: {exc}") from exc

        reply_text = self._extract_reply_text(response)
        provider_request_id = str(getattr(response, "id", "") or "")
        raw_provider_payload = self._extract_raw_payload(response)
        return LLMResponse(
            reply_text=reply_text,
            provider_request_id=provider_request_id,
            raw_provider_payload=raw_provider_payload,
        )

    def _extract_reply_text(self, response: Any) -> str:
        """Извлекает текст ответа из сырого объекта SDK.

        Параметры:
            response: Сырой объект ответа провайдера.

        Возвращает:
            Непустой текст ответа модели.

        Исключения:
            LLMEmptyResponseError: Возникает, если ответ пуст или структура
                не содержит ожидаемого текста.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        choices = getattr(response, "choices", None)
        if not choices:
            raise LLMEmptyResponseError("LLM не вернула ни одного варианта ответа.")

        message = getattr(choices[0], "message", None)
        reply_text = getattr(message, "content", "") if message is not None else ""
        if not isinstance(reply_text, str) or not reply_text.strip():
            raise LLMEmptyResponseError("LLM вернула пустой текст ответа.")
        return reply_text.strip()

    def _extract_raw_payload(self, response: Any) -> dict[str, Any]:
        """Готовит безопасный снимок ответа провайдера для внутренних логов.

        Параметры:
            response: Сырой объект ответа SDK.

        Возвращает:
            Небольшой словарь с идентификатором, model и usage при наличии.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        usage = getattr(response, "usage", None)
        return {
            "id": str(getattr(response, "id", "") or ""),
            "model": str(getattr(response, "model", "") or ""),
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
            if usage is not None
            else None,
        }


def build_platform_llm_settings_snapshot(
    settings: PlatformSettingsLike,
    mode: LLMMode,
) -> PlatformLLMSettingsSnapshot:
    """Строит снимок LLM-параметров из активных настроек платформы.

    Функция нужна для явного преобразования ORM-модели ``PlatformSettings`` в
    стабильный DTO, который далее можно сохранять в snapshot-поля диалога или
    использовать для непосредственного вызова модели.

    Параметры:
        settings: Экземпляр активных глобальных настроек платформы.
        mode: Требуемый режим вызова LLM.

    Возвращает:
        Заполненный ``PlatformLLMSettingsSnapshot``.

    Исключения:
        LLMConfigurationError: Возникает, если обязательные поля настроек
            отсутствуют или режим не поддерживается.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    if not settings.llm_base_url:
        raise LLMConfigurationError("В активных настройках платформы не задан llm_base_url.")
    if not settings.llm_model_name:
        raise LLMConfigurationError("В активных настройках платформы не задан llm_model_name.")

    if mode == LLMMode.GAME:
        max_tokens = settings.llm_game_max_tokens
    elif mode in {LLMMode.ANALYSIS, LLMMode.SYSTEM}:
        max_tokens = settings.llm_analysis_max_tokens
    else:  # pragma: no cover - защитная ветка для будущих расширений.
        raise LLMConfigurationError(f"Неподдерживаемый режим LLM: {mode}.")

    return PlatformLLMSettingsSnapshot(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model_name=settings.llm_model_name,
        temperature=float(settings.llm_temperature),
        top_p=float(settings.llm_top_p),
        max_tokens=max_tokens,
        max_user_message_chars=settings.max_user_message_chars,
        max_game_reply_chars=settings.max_game_reply_chars,
        max_analysis_reply_chars=settings.max_analysis_reply_chars,
    )


def get_active_platform_llm_settings(
    mode: LLMMode,
    settings_loader: Callable[[], PlatformSettingsLike] | None = None,
) -> PlatformLLMSettingsSnapshot:
    """Возвращает снимок активных LLM-настроек платформы.

    Это тонкий helper для сервисного слоя, который централизует чтение
    singleton-записи ``PlatformSettings`` и переводит её в DTO без утечки ORM
    в другие части приложения. Для unit-тестов допускается передать
    ``settings_loader`` и тем самым избежать обязательной загрузки Django ORM.

    Параметры:
        mode: Режим, для которого нужно подобрать ``max_tokens``.
        settings_loader: Необязательный callback, возвращающий объект
            настроек. Если не передан, используется чтение через Django ORM.

    Возвращает:
        Снимок активных LLM-параметров ``PlatformLLMSettingsSnapshot``.

    Исключения:
        LLMConfigurationError: Возникает, если активная запись не найдена,
            если ORM обнаружила несколько активных записей или если loader
            завершился ошибкой.

    Побочные эффекты:
        По умолчанию выполняет запрос к базе данных.
    """
    if settings_loader is not None:
        try:
            settings = settings_loader()
        except LLMIntegrationError:
            raise
        except Exception as exc:
            raise LLMConfigurationError("Не удалось загрузить активные настройки платформы для LLM.") from exc
        return build_platform_llm_settings_snapshot(settings=settings, mode=mode)

    try:
        from apps.platform_config.models import PlatformSettings

        settings = PlatformSettings.objects.get(is_active=True)
    except Exception as exc:
        raise LLMConfigurationError("Не удалось получить активные настройки PlatformSettings для LLM.") from exc
    return build_platform_llm_settings_snapshot(settings=settings, mode=mode)


def build_request_from_platform_settings(
    *,
    mode: LLMMode,
    settings_snapshot: PlatformLLMSettingsSnapshot,
    messages: list[LLMMessage] | tuple[LLMMessage, ...],
) -> LLMRequest:
    """Собирает ``LLMRequest`` из снимка платформенных настроек и сообщений.

    Функция упрощает код прикладных сервисов, которые уже знают режим
    вызова и подготовили список сообщений, но не хотят вручную копировать
    каждое поле настроек в объект запроса.

    Параметры:
        mode: Режим вызова LLM.
        settings_snapshot: Ранее собранный снимок параметров платформы.
        messages: Нормализованная последовательность сообщений.

    Возвращает:
        Экземпляр ``LLMRequest``.

    Исключения:
        ValueError: Может возникнуть из ``LLMRequest`` или ``LLMMessage`` при
            невалидных входных данных.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """
    return LLMRequest(
        mode=mode,
        base_url=settings_snapshot.base_url,
        api_key=settings_snapshot.api_key,
        model_name=settings_snapshot.model_name,
        temperature=settings_snapshot.temperature,
        top_p=settings_snapshot.top_p,
        max_tokens=settings_snapshot.max_tokens,
        messages=tuple(messages),
    )
