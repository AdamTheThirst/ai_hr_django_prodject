"""Модели пользователей и ролей приложения ``accounts``."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimestampedModel, UUIDPublicIdModel

from .managers import UserManager
from .utils import build_avatar_background, build_avatar_letter


class User(UUIDPublicIdModel, TimestampedModel, AbstractBaseUser, PermissionsMixin):
    """Описывает кастомную модель пользователя проекта.

    Модель используется как единый источник данных для аутентификации,
    ролевых ограничений и пользовательского отображения. По спецификации
    логин выполняется по ``email``, никнейм хранится отдельно, а роль и
    дополнительные флаги определяют доступ к административным сценариям.

    Параметры:
        Экземпляр создаётся через ORM, формы Django или менеджер
        ``UserManager``. Основные прикладные поля: ``email``, ``nickname``,
        ``role`` и служебные флаги доступа.

    Возвращает:
        Экземпляр модели ``User``.

    Исключения:
        ValidationError: Возникает при нарушении согласованных ограничений,
            например если главный супер-администратор не имеет роли
            ``superadmin`` или административная роль создана без ``is_staff``.

    Побочные эффекты:
        При сохранении автоматически нормализует email и пересчитывает поля
        текстового аватара ``avatar_letter`` и ``avatar_bg_hex``.
    """

    class Role(models.TextChoices):
        """Перечисляет поддерживаемые роли пользовательского доступа.

        Перечисление используется моделью ``User``, формами, сервисами и
        будущими permission-check'ами, чтобы работать только с разрешённым
        набором ролей, зафиксированным в спецификации.

        Параметры:
            Значения перечисления не принимают пользовательских параметров.

        Возвращает:
            Элементы ``TextChoices`` со строковыми кодами ролей.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """

        USER = "user", "Пользователь"
        ADMIN = "admin", "Администратор"
        SUPERADMIN = "superadmin", "Супер-администратор"

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    nickname = models.CharField(
        max_length=150,
        verbose_name="Никнейм",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name="Роль",
    )
    is_primary_superadmin = models.BooleanField(
        default=False,
        verbose_name="Главный супер-администратор",
    )
    avatar_letter = models.CharField(
        max_length=1,
        default="?",
        editable=False,
        verbose_name="Буква аватара",
    )
    avatar_bg_hex = models.CharField(
        max_length=7,
        default="#E5E7EB",
        editable=False,
        verbose_name="Фон аватара",
    )
    is_seed = models.BooleanField(
        default=False,
        verbose_name="Seed-учётная запись",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Доступ в Django Admin",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата регистрации",
    )
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
        verbose_name="Создано пользователем",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    class Meta:
        """Определяет метаданные и ограничения модели пользователя."""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [
            models.CheckConstraint(
                check=Q(is_primary_superadmin=False) | Q(role=Role.SUPERADMIN),
                name="accounts_user_primary_superadmin_requires_role",
            ),
            models.CheckConstraint(
                check=(
                    (Q(role=Role.USER) & Q(is_staff=False))
                    | (Q(role=Role.ADMIN) & Q(is_staff=True))
                    | (Q(role=Role.SUPERADMIN) & Q(is_staff=True))
                ),
                name="accounts_user_staff_matches_role",
            ),
            models.UniqueConstraint(
                fields=["is_primary_superadmin"],
                condition=Q(is_primary_superadmin=True, role=Role.SUPERADMIN),
                name="accounts_user_single_primary_superadmin",
            ),
        ]
        indexes = [
            models.Index(fields=["role", "is_active"], name="accounts_user_role_active_idx"),
            models.Index(fields=["is_seed"], name="accounts_user_is_seed_idx"),
        ]

    @classmethod
    def staff_roles(cls) -> tuple[str, ...]:
        """Возвращает набор ролей, которым нужен доступ staff-уровня.

        Метод используется менеджером, валидацией и потенциально формами,
        когда нужно единообразно определить, какие продуктовые роли должны
        иметь доступ к административным интерфейсам Django.

        Параметры:
            Явные параметры отсутствуют. Класс передаётся автоматически как
            первый аргумент ``cls``.

        Возвращает:
            Кортеж строковых кодов ролей, для которых ``is_staff`` обязан
            быть установлен в ``True``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return (cls.Role.ADMIN, cls.Role.SUPERADMIN)

    def clean(self) -> None:
        """Проверяет согласованность полей пользователя перед сохранением.

        Метод вызывается формами, административным интерфейсом и из
        переопределённого ``save()`` для централизованной серверной
        валидации критичных инвариантов пользовательской модели.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает при нарушении правил роли,
                ``is_primary_superadmin`` или ``is_staff``.

        Побочные эффекты:
            Нормализует email и пересчитывает аватарные поля в памяти до
            фактического сохранения объекта.
        """
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email or "").lower()
        self.update_avatar_fields()

        if self.is_primary_superadmin and self.role != self.Role.SUPERADMIN:
            raise ValidationError(
                {"is_primary_superadmin": "Главный супер-администратор должен иметь роль superadmin."}
            )

        if self.role in self.staff_roles() and not self.is_staff:
            raise ValidationError({"is_staff": "Административная роль должна иметь is_staff=True."})

        if self.role == self.Role.USER and self.is_staff:
            raise ValidationError({"is_staff": "Обычный пользователь не должен иметь is_staff=True."})

    def update_avatar_fields(self) -> None:
        """Пересчитывает вычисляемые поля текстового аватара пользователя.

        Метод нужен для синхронизации ``avatar_letter`` и ``avatar_bg_hex``
        с текущими значениями никнейма и email без необходимости хранить
        отдельную бизнес-логику в формах или представлениях.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Меняет значения полей ``avatar_letter`` и ``avatar_bg_hex`` в
            памяти текущего экземпляра.
        """
        self.avatar_letter = build_avatar_letter(self.nickname)
        self.avatar_bg_hex = build_avatar_background(self.email)

    def save(self, *args, **kwargs) -> None:
        """Сохраняет пользователя с предварительной валидацией и нормализацией.

        Метод переопределён, чтобы любая запись пользователя, созданная не
        только через формы, но и напрямую через ORM, проходила одинаковую
        серверную валидацию и получала корректные вычисляемые поля аватара.

        Параметры:
            *args: Позиционные аргументы стандартного ``Model.save``.
            **kwargs: Именованные аргументы стандартного ``Model.save``.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Возникает, если модель не проходит ``full_clean``.
            DatabaseError: Возможны стандартные ошибки Django ORM при записи
                в базу данных.

        Побочные эффекты:
            - Запускает ``full_clean()``.
            - Может выполнять SQL-запросы ``INSERT`` или ``UPDATE``.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Возвращает человекочитаемое представление пользователя.

        Метод используется в административных списках, логах и отладочном
        выводе, где нужно быстро идентифицировать запись по никнейму и
        email без дополнительного запроса к связанным данным.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Строку вида ``"Никнейм <email>"``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return f"{self.nickname} <{self.email}>"
