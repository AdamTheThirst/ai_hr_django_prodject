"""Django-тесты модели пользователя приложения ``accounts``."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User


class UserModelTests(TestCase):
    """Проверяет ключевые инварианты кастомной модели пользователя.

    Тестовый набор покрывает базовые ограничения ролей, вычисляемые поля
    аватара и ограничение на единственного главного супер-администратора.

    Параметры:
        Экземпляр класса создаётся встроенным тест-раннером Django.

    Возвращает:
        Экземпляр ``django.test.TestCase``.

    Исключения:
        AssertionError: Возникает при несовпадении фактического и ожидаемого
            поведения модели.

    Побочные эффекты:
        Создаёт временную тестовую базу данных на время выполнения.
    """

    def test_user_manager_populates_avatar_fields(self) -> None:
        """Проверяет автоматическое заполнение вычисляемых полей аватара.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если поля аватара не заполнены.

        Побочные эффекты:
            Создаёт пользователя в тестовой базе данных.
        """
        user = User.objects.create_user(
            email="user@example.com",
            nickname="Алексей",
            password="12345678",
        )

        self.assertEqual(user.avatar_letter, "А")
        self.assertTrue(user.avatar_bg_hex.startswith("#"))

    def test_primary_superadmin_requires_superadmin_role(self) -> None:
        """Проверяет запрет на несогласованную роль главного супер-админа.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при нарушении ограничения.

        Побочные эффекты:
            Побочные эффекты отсутствуют, так как объект не сохраняется.
        """
        user = User(
            email="root-check@example.com",
            nickname="Root",
            role=User.Role.ADMIN,
            is_staff=True,
            is_primary_superadmin=True,
        )
        user.set_password("12345678")

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_user_role_cannot_have_staff_flag(self) -> None:
        """Проверяет запрет ``is_staff`` для обычного пользователя.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при нарушении ограничения.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        user = User(
            email="plain@example.com",
            nickname="Plain",
            role=User.Role.USER,
            is_staff=True,
        )
        user.set_password("12345678")

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_only_one_primary_superadmin_can_exist(self) -> None:
        """Проверяет ограничение на единственного главного супер-админа.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            IntegrityError: Ожидается при попытке создать вторую primary
                superadmin-запись.

        Побочные эффекты:
            Создаёт тестовые записи в базе данных.
        """
        User.objects.create_user(
            email="root1@example.com",
            nickname="Root1",
            password="12345678",
            role=User.Role.SUPERADMIN,
            is_staff=True,
            is_primary_superadmin=True,
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="root2@example.com",
                nickname="Root2",
                password="12345678",
                role=User.Role.SUPERADMIN,
                is_staff=True,
                is_primary_superadmin=True,
            )
