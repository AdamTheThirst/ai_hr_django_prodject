"""Модели игрового диалога и сообщений пользователя."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimestampedModel, UUIDPublicIdModel


class DialogSession(UUIDPublicIdModel, TimestampedModel):
    """Хранит одну игровую сессию пользователя в выбранном сценарии.

    Модель фиксирует весь жизненный цикл диалога: старт, финальный статус,
    причину завершения, снимки контента и эффективные параметры платформы,
    действовавшие на момент запуска. Это позволяет не зависеть от будущих
    изменений сценариев, промтов и глобальных настроек.

    Параметры:
        Экземпляр создаётся через ORM или будущие сервисы запуска сценария.
        Ключевые поля: пользователь, игра, сценарий, использованный промт,
        статус, причина завершения, счётчики сообщений и snapshot-поля.

    Возвращает:
        Экземпляр модели ``DialogSession``.

    Исключения:
        ValidationError: Возникает при несогласованном статусе, причине
            завершения или некорректном наборе обязательных snapshot-полей.

    Побочные эффекты:
        При сохранении запускает полную модельную валидацию.
    """

    class Status(models.TextChoices):
        """Перечисляет допустимые жизненные статусы диалога.

        Параметры:
            Явные параметры не принимаются.

        Возвращает:
            Элементы ``TextChoices`` со строковыми кодами статусов.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """

        ACTIVE = "active", "Активный"
        FINISHED = "finished", "Завершён"
        ABORTED = "aborted", "Прерван"
        ANALYSIS_SKIPPED = "analysis_skipped", "Анализ пропущен"

    class EndedReason(models.TextChoices):
        """Перечисляет причины завершения диалога.

        Параметры:
            Явные параметры не принимаются.

        Возвращает:
            Элементы ``TextChoices`` с кодами причин завершения.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """

        MANUAL_FEEDBACK = "manual_feedback", "Ручное завершение"
        TIMEOUT = "timeout", "Таймаут"
        PAGE_LEAVE = "page_leave", "Уход со страницы"
        INACTIVE_TIMEOUT = "inactive_timeout", "Таймаут неактивности"
        NO_USER_MESSAGES = "no_user_messages", "Нет пользовательских реплик"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Пользователь",
    )
    game = models.ForeignKey(
        "content.Game",
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Игра",
    )
    scenario = models.ForeignKey(
        "content.Scenario",
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Сценарий",
    )
    scenario_prompt_used = models.ForeignKey(
        "content.ScenarioPrompt",
        on_delete=models.PROTECT,
        related_name="dialog_sessions",
        verbose_name="Использованный игровой промт",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Начат",
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Завершён",
    )
    ended_reason = models.CharField(
        max_length=32,
        choices=EndedReason.choices,
        blank=True,
        verbose_name="Причина завершения",
    )
    user_message_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество сообщений пользователя",
    )
    assistant_message_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество сообщений ИИ",
    )
    effective_duration_seconds = models.PositiveIntegerField(
        verbose_name="Зафиксированная длительность в секундах",
    )
    effective_user_message_max_chars = models.PositiveIntegerField(
        verbose_name="Зафиксированный лимит пользовательского сообщения",
    )
    effective_game_reply_max_chars = models.PositiveIntegerField(
        verbose_name="Зафиксированный лимит игрового ответа",
    )
    effective_analysis_reply_max_chars = models.PositiveIntegerField(
        verbose_name="Зафиксированный лимит аналитического ответа",
    )
    effective_llm_model_name = models.CharField(
        max_length=255,
        verbose_name="Зафиксированное имя модели",
    )
    effective_llm_temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.70"),
        verbose_name="Зафиксированная temperature",
    )
    effective_llm_top_p = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.80"),
        verbose_name="Зафиксированный top_p",
    )
    effective_llm_game_max_tokens = models.PositiveIntegerField(
        verbose_name="Зафиксированный game max_tokens",
    )
    effective_llm_analysis_max_tokens = models.PositiveIntegerField(
        verbose_name="Зафиксированный analysis max_tokens",
    )
    conditions_snapshot_text = models.TextField(
        verbose_name="Snapshot условий",
    )
    opening_message_snapshot_text = models.TextField(
        verbose_name="Snapshot стартовой реплики",
    )
    last_client_activity_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последняя активность клиента",
    )
    client_aborted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Сигнал client abort",
    )

    class Meta:
        """Определяет метаданные модели игровой сессии."""

        verbose_name = "Игровая сессия"
        verbose_name_plural = "Игровые сессии"
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status=Status.ACTIVE),
                name="dialogs_single_active_dialog_per_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="dialogs_session_user_status_idx"),
            models.Index(fields=["game"], name="dialogs_session_game_idx"),
            models.Index(fields=["scenario"], name="dialogs_session_scenario_idx"),
            models.Index(fields=["started_at"], name="dialogs_session_started_at_idx"),
        ]

    def clean(self) -> None:
        """Проверяет согласованность жизненного цикла и snapshot-полей диалога.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при несовместимых статусе и причине
                завершения либо при пустых snapshot-полях.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if not (self.conditions_snapshot_text or "").strip():
            raise ValidationError({"conditions_snapshot_text": "Snapshot условий обязателен."})
        if not (self.opening_message_snapshot_text or "").strip():
            raise ValidationError({"opening_message_snapshot_text": "Snapshot стартовой реплики обязателен."})

        reason = self.ended_reason or None
        if self.status == self.Status.ACTIVE:
            if self.ended_at is not None:
                raise ValidationError({"ended_at": "У активного диалога не может быть времени завершения."})
            if reason is not None:
                raise ValidationError({"ended_reason": "У активного диалога не может быть причины завершения."})

        if self.status == self.Status.FINISHED:
            if reason not in {self.EndedReason.MANUAL_FEEDBACK, self.EndedReason.TIMEOUT}:
                raise ValidationError({"ended_reason": "Для finished допустимы только manual_feedback или timeout."})
            if self.ended_at is None:
                raise ValidationError({"ended_at": "Для finished требуется время завершения."})

        if self.status == self.Status.ABORTED:
            if reason not in {self.EndedReason.PAGE_LEAVE, self.EndedReason.INACTIVE_TIMEOUT}:
                raise ValidationError({"ended_reason": "Для aborted допустимы только page_leave или inactive_timeout."})
            if self.ended_at is None:
                raise ValidationError({"ended_at": "Для aborted требуется время завершения."})

        if self.status == self.Status.ANALYSIS_SKIPPED:
            if reason != self.EndedReason.NO_USER_MESSAGES:
                raise ValidationError({"ended_reason": "Для analysis_skipped допустима только причина no_user_messages."})
            if self.ended_at is None:
                raise ValidationError({"ended_at": "Для analysis_skipped требуется время завершения."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет игровую сессию после полной серверной валидации.

        Параметры:
            *args: Позиционные аргументы стандартного ``Model.save``.
            **kwargs: Именованные аргументы стандартного ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при провале ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` и сохраняет объект в БД.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление диалога.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку с email пользователя, сценарием и статусом.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"{self.user.email} — {self.scenario.title} ({self.status})"


class DialogMessage(models.Model):
    """Хранит одно сообщение внутри игрового диалога.

    Модель отражает историю переписки пользователя и персонажа ИИ. Она
    хранит последовательность, роль отправителя, текст и технический
    идентификатор LLM-вызова при наличии.

    Параметры:
        Экземпляр создаётся ORM или будущими сервисами отправки сообщений.
        Основные поля: ``dialog``, ``sequence_no``, ``role`` и ``text``.

    Возвращает:
        Экземпляр модели ``DialogMessage``.

    Исключения:
        ValidationError: Возникает при пустом тексте, несовпадении длины
            сообщения или нарушении лимита для пользовательской реплики.

    Побочные эффекты:
        При сохранении запускает полную модельную валидацию.
    """

    class Role(models.TextChoices):
        """Перечисляет роли отправителей сообщений в таблице диалога.

        Параметры:
            Явные параметры не принимаются.

        Возвращает:
            Элементы ``TextChoices`` со строковыми кодами ролей.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """

        ASSISTANT = "assistant", "Ассистент"
        USER = "user", "Пользователь"

    dialog = models.ForeignKey(
        DialogSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Диалог",
    )
    sequence_no = models.PositiveIntegerField(
        verbose_name="Порядковый номер",
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        verbose_name="Роль",
    )
    text = models.TextField(
        verbose_name="Текст",
    )
    char_count = models.PositiveIntegerField(
        verbose_name="Количество символов",
    )
    llm_request_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Идентификатор LLM-запроса",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )

    class Meta:
        """Определяет метаданные модели сообщения диалога."""

        verbose_name = "Сообщение диалога"
        verbose_name_plural = "Сообщения диалога"
        ordering = ["dialog", "sequence_no"]
        constraints = [
            models.UniqueConstraint(fields=["dialog", "sequence_no"], name="dialogs_message_unique_sequence"),
        ]
        indexes = [
            models.Index(fields=["dialog", "sequence_no"], name="dialogs_message_dialog_sequence_idx"),
        ]

    def clean(self) -> None:
        """Проверяет корректность текста и его длины для сообщения.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при пустом тексте, неверном
                ``char_count`` или превышении лимита сообщения пользователя.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        normalized_text = self.text or ""
        if not normalized_text.strip():
            raise ValidationError({"text": "Текст сообщения не может быть пустым."})
        if self.char_count != len(normalized_text):
            raise ValidationError({"char_count": "char_count должен совпадать с фактической длиной текста."})
        if self.role == self.Role.USER and self.char_count > self.dialog.effective_user_message_max_chars:
            raise ValidationError({"text": "Сообщение пользователя превышает зафиксированный лимит."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет сообщение после полной валидации.

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
        """Возвращает человекочитаемое представление сообщения диалога.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Короткую строку с номером сообщения и ролью отправителя.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"#{self.sequence_no} {self.role}"
