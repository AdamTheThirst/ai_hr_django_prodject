"""Модели анализа диалога и результатов по критериям."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel, UUIDPublicIdModel


class AnalysisRun(UUIDPublicIdModel, TimestampedModel):
    """Фиксирует один запуск анализа для конкретного диалога.

    Модель отделяет жизненный цикл анализа от жизненного цикла самого
    диалога и хранит технический статус, количество попыток и сведения об
    ошибке без перегрузки таблицы ``DialogSession``.

    Параметры:
        Экземпляр создаётся через ORM или будущий сервис аналитики. Основные
        поля: ``dialog``, ``status``, ``started_at``, ``finished_at`` и
        технические поля ошибок.

    Возвращает:
        Экземпляр модели ``AnalysisRun``.

    Исключения:
        ValidationError: Возникает при несогласованном статусе анализа и
            состоянии диалога.

    Побочные эффекты:
        При сохранении запускает полную модельную валидацию.
    """

    class Status(models.TextChoices):
        """Перечисляет допустимые статусы запуска анализа.

        Параметры:
            Явные параметры не принимаются.

        Возвращает:
            Элементы ``TextChoices`` со строковыми кодами статусов.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """

        PENDING = "pending", "В очереди"
        RUNNING = "running", "Выполняется"
        COMPLETED = "completed", "Завершён"
        FAILED = "failed", "Ошибка"
        SKIPPED = "skipped", "Пропущен"

    dialog = models.OneToOneField(
        "dialogs.DialogSession",
        on_delete=models.CASCADE,
        related_name="analysis_run",
        verbose_name="Диалог",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Запущен",
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Завершён",
    )
    llm_attempt_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество LLM-вызовов",
    )
    error_code = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Код ошибки",
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Описание ошибки",
    )

    class Meta:
        """Определяет метаданные модели запуска анализа."""

        verbose_name = "Запуск анализа"
        verbose_name_plural = "Запуски анализа"
        ordering = ["-started_at"]

    def clean(self) -> None:
        """Проверяет согласованность статуса анализа и диалога.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если финальный статус анализа не
                согласован с ``finished_at`` или статусом диалога.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if self.status in {self.Status.COMPLETED, self.Status.FAILED, self.Status.SKIPPED} and self.finished_at is None:
            raise ValidationError({"finished_at": "Для финального статуса анализа требуется время завершения."})
        if self.status in {self.Status.PENDING, self.Status.RUNNING} and self.finished_at is not None:
            raise ValidationError({"finished_at": "pending/running не должны иметь времени завершения."})
        if self.status == self.Status.SKIPPED and self.dialog.status != self.dialog.Status.ANALYSIS_SKIPPED:
            raise ValidationError({"status": "Статус skipped допустим только для диалога analysis_skipped."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет запуск анализа после полной валидации.

        Параметры:
            *args: Позиционные аргументы ``Model.save``.
            **kwargs: Именованные аргументы ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при провале ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` и сохраняет объект.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление запуска анализа.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку со статусом анализа и идентификатором диалога.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"Анализ {self.dialog.public_id} ({self.status})"


class AnalysisResult(TimestampedModel):
    """Хранит результат одного аналитического критерия внутри запуска анализа.

    Модель фиксирует snapshot критерия, числовой рейтинг, текст анализа,
    исходный ответ LLM и статус валидации JSON-контракта. Благодаря
    snapshot-полям исторические результаты не меняются при редактировании
    исходных промтов в админке.

    Параметры:
        Экземпляр создаётся через ORM или будущий аналитический сервис.
        Основные поля: ``analysis_run``, ``analysis_prompt``, snapshot-поля,
        рейтинг, текст анализа и статус валидации.

    Возвращает:
        Экземпляр модели ``AnalysisResult``.

    Исключения:
        ValidationError: Возникает при выходе рейтинга за пределы шкалы или
            при пустом тексте анализа.

    Побочные эффекты:
        При сохранении запускает полную модельную валидацию.
    """

    class ValidationStatus(models.TextChoices):
        """Перечисляет статусы валидации ответа аналитической LLM.

        Параметры:
            Явные параметры не принимаются.

        Возвращает:
            Элементы ``TextChoices`` со строковыми кодами статусов.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """

        VALID = "valid", "Валиден"
        INVALID_JSON = "invalid_json", "Невалидный JSON"
        INVALID_SCHEMA = "invalid_schema", "Невалидная схема"
        FALLBACK_SAVED = "fallback_saved", "Сохранён fallback"

    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Запуск анализа",
    )
    analysis_prompt = models.ForeignKey(
        "content.AnalysisPrompt",
        on_delete=models.PROTECT,
        related_name="analysis_results",
        verbose_name="Аналитический промт",
    )
    sort_order_snapshot = models.PositiveIntegerField(
        verbose_name="Snapshot порядка",
    )
    alias_snapshot = models.SlugField(
        verbose_name="Snapshot alias",
    )
    title_snapshot = models.CharField(
        max_length=255,
        verbose_name="Snapshot названия",
    )
    header_snapshot_text = models.CharField(
        max_length=255,
        verbose_name="Snapshot заголовка",
    )
    comment_snapshot_text = models.TextField(
        blank=True,
        verbose_name="Snapshot комментария",
    )
    rating = models.SmallIntegerField(
        verbose_name="Рейтинг",
    )
    rating_min = models.SmallIntegerField(
        verbose_name="Минимум рейтинга",
    )
    rating_max = models.SmallIntegerField(
        verbose_name="Максимум рейтинга",
    )
    analysis_text = models.TextField(
        verbose_name="Текст анализа",
    )
    raw_llm_response_text = models.TextField(
        blank=True,
        verbose_name="Сырой ответ LLM",
    )
    parsed_json_snapshot = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Snapshot валидного JSON",
    )
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.VALID,
        verbose_name="Статус валидации",
    )
    validation_error_message = models.TextField(
        blank=True,
        verbose_name="Ошибка валидации",
    )
    llm_attempt_count = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество попыток LLM",
    )

    class Meta:
        """Определяет метаданные модели результата анализа."""

        verbose_name = "Результат анализа"
        verbose_name_plural = "Результаты анализа"
        ordering = ["analysis_run", "sort_order_snapshot", "id"]
        constraints = [
            models.UniqueConstraint(fields=["analysis_run", "analysis_prompt"], name="analysis_result_unique_prompt_per_run"),
        ]
        indexes = [
            models.Index(fields=["analysis_run", "sort_order_snapshot"], name="analysis_result_run_sort_idx"),
        ]

    def clean(self) -> None:
        """Проверяет корректность рейтинга и обязательных snapshot-полей.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если рейтинг вне диапазона или текст
                анализа пустой.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if self.rating_min > self.rating_max:
            raise ValidationError({"rating_max": "Максимум рейтинга не может быть меньше минимума."})
        if not (self.rating_min <= self.rating <= self.rating_max):
            raise ValidationError({"rating": "Рейтинг должен лежать в диапазоне [rating_min, rating_max]."})
        if not (self.analysis_text or "").strip():
            raise ValidationError({"analysis_text": "Текст анализа обязателен."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет результат анализа после полной валидации.

        Параметры:
            *args: Позиционные аргументы ``Model.save``.
            **kwargs: Именованные аргументы ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при провале ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` и сохраняет запись в БД.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление результата анализа.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку с alias критерия и рейтингом.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"{self.alias_snapshot}: {self.rating}/{self.rating_max}"
