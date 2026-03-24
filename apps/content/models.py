"""Контентные модели игр, сценариев и промтов."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import ArchivableModel, OwnedModel, TimestampedModel, UUIDPublicIdModel


class Game(UUIDPublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Описывает игру как верхний контейнер сценариев и аналитических критериев.

    Модель используется в пользовательской навигации и административном
    управлении контентом. Игра хранит общие свойства набора сценариев и
    выступает владельцем аналитических промтов, общих для всех сценариев
    внутри этой игры.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``slug``, ``title``, ``short_description``, ``sort_order`` и
        признаки публикации/архивации.

    Возвращает:
        Экземпляр модели ``Game``.

    Исключения:
        ValidationError: Может возникнуть при нарушении ограничений модели,
            например если обязательные поля не заполнены.

    Побочные эффекты:
        Побочные эффекты отсутствуют; модель хранит только состояние игры.
    """

    slug = models.SlugField(
        unique=True,
        verbose_name="Slug",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    short_description = models.TextField(
        blank=True,
        verbose_name="Краткое описание",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок показа",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликована",
    )

    class Meta:
        """Определяет метаданные модели игры."""

        verbose_name = "Игра"
        verbose_name_plural = "Игры"
        ordering = ["sort_order", "title"]
        indexes = [
            models.Index(fields=["is_published", "is_archived"], name="content_game_publish_arch_idx"),
        ]

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление игры.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Название игры.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return self.title


class ScenarioMediaAsset(UUIDPublicIdModel, ArchivableModel, TimestampedModel):
    """Хранит переиспользуемый медиа-ресурс сценария.

    В первой версии модель предназначена прежде всего для локально
    сохранённых изображений в ``MEDIA_ROOT``, но архитектурно допускает и
    другие типы файлов. Ресурс может использоваться несколькими сценариями
    и хранить ссылку на предыдущую версию.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``title``, ``file``, служебные метаданные файла и ссылки на
        пользователя-загрузчика и предыдущую версию.

    Возвращает:
        Экземпляр модели ``ScenarioMediaAsset``.

    Исключения:
        ValidationError: Может возникнуть при нарушении ограничений модели.

    Побочные эффекты:
        При сохранении может создавать или обновлять запись о файле в БД.
    """

    title = models.CharField(
        max_length=255,
        verbose_name="Название ресурса",
    )
    file = models.FileField(
        upload_to="scenario_media/",
        verbose_name="Файл",
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Исходное имя файла",
    )
    mime_type = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="MIME-тип",
    )
    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Размер файла в байтах",
    )
    checksum_sha256 = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="SHA256",
    )
    previous_version = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="next_versions",
        verbose_name="Предыдущая версия",
    )
    uploaded_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_media_assets",
        verbose_name="Загрузил пользователь",
    )

    class Meta:
        """Определяет метаданные модели медиа-ресурса."""

        verbose_name = "Медиа-ресурс сценария"
        verbose_name_plural = "Медиа-ресурсы сценариев"
        ordering = ["title", "created_at"]
        indexes = [
            models.Index(fields=["is_archived", "created_at"], name="content_media_arch_created_idx"),
        ]

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление медиа-ресурса.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Название ресурса.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return self.title


class Scenario(UUIDPublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Описывает конкретный сценарий внутри выбранной игры.

    Сценарий определяет условия диалога, стартовую реплику персонажа,
    привязку к медиа-ресурсу и порядок отображения кнопки запуска внутри
    игры. Именно эта модель будет использоваться пользователем при выборе
    конкретной тренируемой ситуации.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``game``, ``slug``, ``title``, ``conditions_text``,
        ``opening_message_text`` и публикационные флаги.

    Возвращает:
        Экземпляр модели ``Scenario``.

    Исключения:
        ValidationError: Возникает при отсутствии обязательных текстов
            сценария или при нарушении ограничений модели.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="scenarios",
        verbose_name="Игра",
    )
    slug = models.SlugField(
        verbose_name="Slug",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    short_description = models.TextField(
        blank=True,
        verbose_name="Краткое описание",
    )
    conditions_text = models.TextField(
        verbose_name="Текст условий",
    )
    opening_message_text = models.TextField(
        verbose_name="Стартовая реплика",
    )
    media_asset = models.ForeignKey(
        ScenarioMediaAsset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scenarios",
        verbose_name="Медиа-ресурс",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок показа",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Опубликован",
    )

    class Meta:
        """Определяет метаданные модели сценария."""

        verbose_name = "Сценарий"
        verbose_name_plural = "Сценарии"
        ordering = ["game__sort_order", "sort_order", "title"]
        constraints = [
            models.UniqueConstraint(fields=["game", "slug"], name="content_scenario_unique_game_slug"),
        ]
        indexes = [
            models.Index(fields=["game", "sort_order"], name="content_scenario_game_sort_idx"),
            models.Index(fields=["is_published", "is_archived"], name="content_scenario_publish_arch_idx"),
        ]

    def clean(self) -> None:
        """Валидирует обязательные тексты сценария и согласованность полей.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если обязательные тексты пусты или
                состоят только из пробелов.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if not (self.conditions_text or "").strip():
            raise ValidationError({"conditions_text": "Текст условий сценария обязателен."})
        if not (self.opening_message_text or "").strip():
            raise ValidationError({"opening_message_text": "Стартовая реплика персонажа обязательна."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет сценарий после полной серверной валидации.

        Параметры:
            *args: Позиционные аргументы стандартного ``Model.save``.
            **kwargs: Именованные аргументы стандартного ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если сценарий не проходит ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` перед записью в базу данных.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление сценария.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку вида ``"<игра>: <сценарий>"``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"{self.game.title}: {self.title}"


class ScenarioPrompt(UUIDPublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Хранит версию игрового промта конкретного сценария.

    Модель отделяет ролевой игровой промт от стартовой реплики персонажа и
    позволяет хранить историю изменений без подмены уже использованного
    содержимого в прошлых диалогах.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``scenario``, ``title``, ``prompt_text`` и ``is_active``.

    Возвращает:
        Экземпляр модели ``ScenarioPrompt``.

    Исключения:
        ValidationError: Возникает при попытке сохранить архивную активную
            запись или пустой текст промта.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        related_name="scenario_prompts",
        verbose_name="Сценарий",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название версии",
    )
    prompt_text = models.TextField(
        verbose_name="Текст промта",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        """Определяет метаданные модели игрового промта."""

        verbose_name = "Игровой промт"
        verbose_name_plural = "Игровые промты"
        ordering = ["scenario", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["scenario"],
                condition=Q(is_active=True),
                name="content_scenario_prompt_single_active_per_scenario",
            ),
        ]
        indexes = [
            models.Index(fields=["scenario", "is_active"], name="content_scenario_prompt_active_idx"),
        ]

    def clean(self) -> None:
        """Проверяет согласованность активности и архивного состояния промта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если текст пустой или архивная
                запись помечена активной.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if not (self.prompt_text or "").strip():
            raise ValidationError({"prompt_text": "Текст игрового промта обязателен."})
        if self.is_archived and self.is_active:
            raise ValidationError({"is_active": "Архивный игровой промт не может быть активным."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет игровой промт после полной валидации.

        Параметры:
            *args: Позиционные аргументы ``Model.save``.
            **kwargs: Именованные аргументы ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при провале ``full_clean``.
            DatabaseError: Возможны стандартные ошибки ORM.

        Побочные эффекты:
            Запускает ``full_clean()`` перед записью в базу.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление игрового промта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Название версии промта.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return self.title


class AnalysisPrompt(UUIDPublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Хранит один аналитический критерий, общий для игры и её сценариев.

    Модель задаёт отдельный критерий анализа диалога: текст промта,
    отображаемый заголовок, технический alias и границы рейтинга.
    Несколько таких записей образуют набор аналитики игры.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``game``, ``alias``, ``title``, ``header_text``,
        ``prompt_text``, ``sort_order`` и диапазон рейтинга.

    Возвращает:
        Экземпляр модели ``AnalysisPrompt``.

    Исключения:
        ValidationError: Возникает при некорректном диапазоне рейтинга или
            попытке сохранить архивный активный промт.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="analysis_prompts",
        verbose_name="Игра",
    )
    alias = models.SlugField(
        verbose_name="Alias",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название критерия",
    )
    header_text = models.CharField(
        max_length=255,
        verbose_name="Заголовок карточки",
    )
    comment_text = models.TextField(
        blank=True,
        verbose_name="Комментарий для админки",
    )
    prompt_text = models.TextField(
        verbose_name="Текст аналитического промта",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок запуска",
    )
    min_rating = models.SmallIntegerField(
        default=0,
        verbose_name="Минимальный балл",
    )
    max_rating = models.SmallIntegerField(
        default=5,
        verbose_name="Максимальный балл",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        """Определяет метаданные модели аналитического промта."""

        verbose_name = "Аналитический промт"
        verbose_name_plural = "Аналитические промты"
        ordering = ["game", "sort_order", "title"]
        constraints = [
            models.UniqueConstraint(fields=["game", "alias"], name="content_analysis_prompt_unique_alias"),
            models.UniqueConstraint(fields=["game", "sort_order"], name="content_analysis_prompt_unique_sort_order"),
            models.CheckConstraint(check=Q(min_rating__lte=models.F("max_rating")), name="content_analysis_prompt_valid_rating_range"),
        ]
        indexes = [
            models.Index(fields=["game", "sort_order", "is_active"], name="content_analysis_prompt_active_idx"),
        ]

    def clean(self) -> None:
        """Проверяет корректность диапазона оценок и статуса промта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если диапазон рейтинга некорректен,
                текст пустой или архивная запись помечена активной.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if self.min_rating > self.max_rating:
            raise ValidationError({"max_rating": "Максимальный балл не может быть меньше минимального."})
        if not (self.prompt_text or "").strip():
            raise ValidationError({"prompt_text": "Текст аналитического промта обязателен."})
        if self.is_archived and self.is_active:
            raise ValidationError({"is_active": "Архивный аналитический промт не может быть активным."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет аналитический промт после полной валидации.

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
        """Возвращает человекочитаемое представление аналитического промта.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Название аналитического критерия.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return self.title


class SystemPrompt(UUIDPublicIdModel, ArchivableModel, OwnedModel, TimestampedModel):
    """Хранит глобальный служебный системный промт платформы.

    Модель предназначена для системных промтов, которые используются не в
    игровом чате напрямую, а во внутренних технических сценариях платформы,
    например для генерации служебных аналитических метаданных.

    Параметры:
        Экземпляр создаётся через ORM или административные формы. Основные
        поля: ``key``, ``title``, ``prompt_text`` и ``is_active``.

    Возвращает:
        Экземпляр модели ``SystemPrompt``.

    Исключения:
        ValidationError: Возникает при пустом тексте или при попытке сделать
            архивную запись активной.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    key = models.SlugField(
        verbose_name="Ключ",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    prompt_text = models.TextField(
        verbose_name="Текст системного промта",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        """Определяет метаданные модели системного промта."""

        verbose_name = "Системный промт"
        verbose_name_plural = "Системные промты"
        ordering = ["key", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["key"],
                condition=Q(is_active=True),
                name="content_system_prompt_single_active_per_key",
            ),
        ]
        indexes = [
            models.Index(fields=["key", "is_active"], name="content_system_prompt_key_active_idx"),
        ]

    def clean(self) -> None:
        """Проверяет согласованность системного промта перед сохранением.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при пустом тексте или активном
                архивном состоянии.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        super().clean()
        if not (self.prompt_text or "").strip():
            raise ValidationError({"prompt_text": "Текст системного промта обязателен."})
        if self.is_archived and self.is_active:
            raise ValidationError({"is_active": "Архивный системный промт не может быть активным."})

    def save(self, *args, **kwargs) -> None:
        """Сохраняет системный промт после полной валидации.

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
        """Возвращает человекочитаемое представление системного промта.

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
