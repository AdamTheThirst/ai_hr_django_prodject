"""Глобальные настройки платформы и редактируемые UI-тексты."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import ArchivableModel, TimestampedModel


class PlatformSettings(TimestampedModel):
    """Хранит глобальные настройки платформы как singleton-конфигурацию.

    Модель используется для таймеров, лимитов сообщений и параметров LLM,
    которые должны централизованно управляться супер-администратором без
    изменения исходного кода.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля включают таймеры, лимиты длины сообщений и параметры LLM.

    Возвращает:
        Экземпляр модели ``PlatformSettings``.

    Исключения:
        ValidationError: Возникает при нарушении согласованных диапазонов,
            singleton-логики или фиксированных рамок V1.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активная запись",
    )
    default_dialog_duration_minutes = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Глобальная длительность диалога по умолчанию.",
        verbose_name="Длительность диалога по умолчанию",
    )
    user_timer_min_minutes = models.PositiveSmallIntegerField(
        default=5,
        help_text="Нижняя граница будущей пользовательской настройки таймера.",
        verbose_name="Минимум пользовательского таймера",
    )
    user_timer_max_minutes = models.PositiveSmallIntegerField(
        default=20,
        help_text="Верхняя граница будущей пользовательской настройки таймера.",
        verbose_name="Максимум пользовательского таймера",
    )
    default_show_timer = models.BooleanField(
        default=True,
        verbose_name="Показывать таймер по умолчанию",
    )
    max_user_message_chars = models.PositiveIntegerField(
        default=2500,
        validators=[MinValueValidator(1)],
        help_text="Серверный лимит длины пользовательского сообщения.",
        verbose_name="Лимит пользовательского сообщения",
    )
    max_game_reply_chars = models.PositiveIntegerField(
        default=2500,
        validators=[MinValueValidator(1)],
        help_text="Лимит длины игрового ответа LLM.",
        verbose_name="Лимит игрового ответа",
    )
    max_analysis_reply_chars = models.PositiveIntegerField(
        default=5000,
        validators=[MinValueValidator(1)],
        help_text="Лимит длины аналитического ответа LLM.",
        verbose_name="Лимит аналитического ответа",
    )
    llm_base_url = models.URLField(
        help_text="Базовый URL OpenAI-compatible/vLLM сервера.",
        verbose_name="LLM base URL",
    )
    llm_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ключ доступа к LLM. Не должен выводиться в открытом виде во фронтенде и логах.",
        verbose_name="LLM API key",
    )
    llm_model_name = models.CharField(
        max_length=255,
        default="Qwen/Qwen3-32B",
        help_text="Имя модели LLM по умолчанию.",
        verbose_name="Имя модели LLM",
    )
    llm_temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.70"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("2.00"))],
        help_text="Температура генерации для LLM.",
        verbose_name="LLM temperature",
    )
    llm_top_p = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.80"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))],
        help_text="Параметр top_p для LLM.",
        verbose_name="LLM top_p",
    )
    llm_game_max_tokens = models.PositiveIntegerField(
        default=1024,
        validators=[MinValueValidator(1)],
        help_text="Ограничение max_tokens для игрового режима.",
        verbose_name="Game max_tokens",
    )
    llm_analysis_max_tokens = models.PositiveIntegerField(
        default=1024,
        validators=[MinValueValidator(1)],
        help_text="Ограничение max_tokens для аналитического режима.",
        verbose_name="Analysis max_tokens",
    )
    client_abort_grace_seconds = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Окно ожидания после клиентского разрыва соединения.",
        verbose_name="Ожидание после abort",
    )

    class Meta:
        """Определяет метаданные singleton-модели настроек платформы."""

        verbose_name = "Настройки платформы"
        verbose_name_plural = "Настройки платформы"
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="platform_config_single_active_settings",
            ),
        ]

    def clean(self) -> None:
        """Проверяет согласованность глобальных настроек платформы.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при нарушении рамок V1 для таймеров
                или если минимальное и максимальное значения несовместимы.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if self.user_timer_min_minutes != 5:
            raise ValidationError({"user_timer_min_minutes": "В V1 нижняя граница пользовательского таймера должна оставаться равной 5 минутам."})
        if self.user_timer_max_minutes != 20:
            raise ValidationError({"user_timer_max_minutes": "В V1 верхняя граница пользовательского таймера должна оставаться равной 20 минутам."})
        if self.user_timer_min_minutes >= self.user_timer_max_minutes:
            raise ValidationError({"user_timer_max_minutes": "Максимум пользовательского таймера должен быть больше минимума."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет настройки платформы после полной валидации.

        Параметры:
            *args: Позиционные аргументы ``Model.save``.
            **kwargs: Именованные аргументы ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при провале ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` перед записью в базу данных.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление записи настроек.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку со статусом активности записи настроек.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return "Активные настройки платформы" if self.is_active else "Неактивные настройки платформы"


class UIText(ArchivableModel, TimestampedModel):
    """Хранит редактируемые строки пользовательского интерфейса.

    Модель нужна для UI-элементов, тексты которых должны изменяться через
    административный интерфейс без пересборки кода: кнопки, сообщения,
    заглушки и другие согласованные пользовательские строки.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``key``, ``title``, ``text_value`` и ``description``.

    Возвращает:
        Экземпляр модели ``UIText``.

    Исключения:
        ValidationError: Возникает, если текст или ключ заполнены
            некорректно.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    key = models.SlugField(
        unique=True,
        verbose_name="Ключ",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    text_value = models.TextField(
        verbose_name="Текст",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_ui_texts",
        verbose_name="Изменено пользователем",
    )

    class Meta:
        """Определяет метаданные модели UI-текста."""

        verbose_name = "UI-текст"
        verbose_name_plural = "UI-тексты"
        ordering = ["key"]

    def clean(self) -> None:
        """Проверяет содержимое UI-текста перед сохранением.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если текстовое значение пустое.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if not (self.text_value or "").strip():
            raise ValidationError({"text_value": "Значение UI-текста не может быть пустым."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет UI-текст после полной валидации.

        Параметры:
            *args: Позиционные аргументы ``Model.save``.
            **kwargs: Именованные аргументы ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при провале ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` перед сохранением.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление UI-текста.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку вида ``"<key>: <title>"``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"{self.key}: {self.title}"
