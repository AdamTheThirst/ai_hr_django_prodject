"""Менеджеры модели пользователя приложения ``accounts``."""

from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager

from .utils import build_avatar_background, build_avatar_letter


class UserManager(BaseUserManager):
    """Управляет созданием пользователей и административных учётных записей.

    Менеджер нужен кастомной модели пользователя, где логин строится по
    ``email``, а дополнительные поля ролей и аватара должны заполняться
    согласованным способом.

    Параметры:
        Экземпляр менеджера создаётся Django автоматически и не принимает
        пользовательских параметров.

    Возвращает:
        Экземпляр менеджера ``UserManager`` для операций ORM.

    Исключения:
        ValueError: Возникает, если при создании пользователя не передан
            обязательный email или никнейм.

    Побочные эффекты:
        Методы менеджера создают и сохраняют записи пользователей в базе
        данных, а также хэшируют пароль через стандартный механизм Django.
    """

    use_in_migrations = True

    def _prepare_user(self, email: str, nickname: str, **extra_fields):
        """Подготавливает экземпляр пользователя перед сохранением.

        Внутренний метод используется общими сценариями создания обычных и
        административных пользователей, чтобы нормализовать email и сразу
        вычислить поля текстового аватара.

        Параметры:
            email: Email пользователя, используемый как логин.
            nickname: Отображаемый никнейм пользователя.
            **extra_fields: Дополнительные поля модели пользователя.

        Возвращает:
            Несохранённый экземпляр пользовательской модели.

        Исключения:
            ValueError: Возникает, если email или nickname отсутствуют.

        Побочные эффекты:
            Побочные эффекты отсутствуют. Метод только создаёт объект в
            памяти и не пишет данные в базу.
        """
        if not email:
            raise ValueError("Невозможно создать пользователя без email.")
        if not nickname:
            raise ValueError("Невозможно создать пользователя без никнейма.")

        normalized_email = self.normalize_email(email).lower()
        extra_fields.setdefault("avatar_letter", build_avatar_letter(nickname))
        extra_fields.setdefault("avatar_bg_hex", build_avatar_background(normalized_email))
        return self.model(email=normalized_email, nickname=nickname, **extra_fields)

    def create_user(self, email: str, nickname: str, password: str | None = None, **extra_fields):
        """Создаёт обычного пользователя или административную запись по параметрам.

        Метод используется регистрацией, seed-механикой и внутренними
        административными сценариями создания пользователей.

        Параметры:
            email: Email пользователя, выступающий логином.
            nickname: Отображаемое имя пользователя.
            password: Пароль в открытом виде, который будет захэширован.
            **extra_fields: Дополнительные атрибуты модели, включая роль,
                флаги активности и служебные признаки.

        Возвращает:
            Сохранённый экземпляр пользовательской модели.

        Исключения:
            ValueError: Возникает, если обязательные поля не переданы.
            ValidationError: Может возникнуть на этапе ``save()``, если
                заполненные данные нарушают ограничения модели.

        Побочные эффекты:
            - Хэширует пароль пользователя.
            - Сохраняет запись в базу данных.
        """
        role = extra_fields.setdefault(self.model.role.field.name, self.model.Role.USER)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", role in self.model.staff_roles())
        extra_fields.setdefault("is_superuser", False)
        user = self._prepare_user(email=email, nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        nickname: str,
        password: str | None = None,
        **extra_fields,
    ):
        """Создаёт техническую суперпользовательскую учётную запись Django.

        Метод нужен для команды ``createsuperuser`` и локальной настройки
        Django Admin. Он не делает пользователя главным супер-администратором
        продукта автоматически, но назначает ему роль ``superadmin`` и
        технические флаги доступа Django.

        Параметры:
            email: Email учётной записи.
            nickname: Отображаемый никнейм.
            password: Пароль в открытом виде.
            **extra_fields: Дополнительные поля модели.

        Возвращает:
            Сохранённый экземпляр суперпользователя.

        Исключения:
            ValueError: Возникает, если обязательные технические флаги
                были переданы в противоречивом состоянии.
            ValidationError: Может возникнуть из модели при сохранении.

        Побочные эффекты:
            Хэширует пароль и сохраняет запись в базе данных.
        """
        extra_fields.setdefault(self.model.role.field.name, self.model.Role.SUPERADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_primary_superadmin", False)

        if extra_fields[self.model.role.field.name] != self.model.Role.SUPERADMIN:
            raise ValueError("Суперпользователь Django должен иметь роль superadmin.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь Django должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь Django должен иметь is_superuser=True.")

        return self.create_user(email=email, nickname=nickname, password=password, **extra_fields)
