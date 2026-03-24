"""Smoke-тесты базовой маршрутизации и каркаса проекта."""

from django.test import TestCase
from django.urls import reverse


class BaseRoutingSmokeTests(TestCase):
    """Проверяет доступность стартовых маршрутов каркаса проекта.

    Набор тестов используется на первой итерации, чтобы убедиться в
    корректном подключении URL, шаблонов и базовых приложений без
    реализации бизнес-логики предметной области.

    Параметры:
        Тестовый класс не принимает пользовательских параметров. Django
        создаёт и управляет его экземпляром самостоятельно.

    Возвращает:
        Экземпляр ``TestCase`` для запуска встроенным тест-раннером Django.

    Исключения:
        Специальные исключения не генерируются. Падение теста означает,
        что маршрут или шаблон настроены некорректно.

    Побочные эффекты:
        Создаёт временную тестовую базу данных на время выполнения тестов.
    """

    def test_home_page_is_available(self) -> None:
        """Проверяет, что корневая страница проекта отвечает кодом 200.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``. Результат проверки выражается через утверждения теста.

        Исключения:
            AssertionError: Возникает, если страница недоступна или код
                ответа отличается от ожидаемого.

        Побочные эффекты:
            Выполняет HTTP-запрос к тестовому клиенту Django.
        """
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)

    def test_health_page_is_available(self) -> None:
        """Проверяет, что страница проверки доступности отвечает кодом 200.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если маршрут настроен неверно.

        Побочные эффекты:
            Выполняет запрос к тестовому HTTP-клиенту Django.
        """
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)

    def test_placeholder_sections_are_available(self) -> None:
        """Проверяет доступность ключевых placeholder-маршрутов каркаса.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если любой из проверяемых маршрутов
                недоступен.

        Побочные эффекты:
            Выполняет серию HTTP-запросов к тестовому клиенту Django.
        """
        urls = [
            reverse("accounts:login"),
            reverse("content:game-list"),
            reverse("dialogs:placeholder"),
            reverse("adminpanel:dashboard"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
