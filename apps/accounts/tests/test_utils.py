"""Pure Python тесты утилит текстового аватара пользователя."""

from __future__ import annotations

import unittest

from apps.accounts.utils import AVATAR_BACKGROUND_PALETTE, build_avatar_background, build_avatar_letter


class AvatarUtilsTests(unittest.TestCase):
    """Проверяет детерминированные вычисления текстового аватара.

    Эти тесты не зависят от Django и нужны как минимальная проверка
    прикладной логики, которую можно выполнить даже в среде без
    установленного фреймворка.

    Параметры:
        Экземпляры класса создаются тестовым раннером ``unittest``.

    Возвращает:
        Экземпляр ``unittest.TestCase``.

    Исключения:
        AssertionError: Возникает, если вычисления буквы или цвета не
            соответствуют ожидаемому поведению.

    Побочные эффекты:
        Побочные эффекты отсутствуют.
    """

    def test_build_avatar_letter_uses_first_visible_character(self) -> None:
        """Проверяет извлечение первой значимой буквы из никнейма.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если функция вернула неверную букву.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.assertEqual(build_avatar_letter("  алексей"), "А")

    def test_build_avatar_letter_returns_fallback_for_blank_value(self) -> None:
        """Проверяет возврат запасного символа для пустого никнейма.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если запасной символ отличается от
                ожидаемого.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        self.assertEqual(build_avatar_letter("   "), "?")

    def test_build_avatar_background_is_deterministic_and_uses_palette(self) -> None:
        """Проверяет детерминированность выбора цвета и принадлежность палитре.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            AssertionError: Возникает, если цвет нестабилен или не входит в
                разрешённую палитру.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        first_value = build_avatar_background("user@example.com")
        second_value = build_avatar_background("user@example.com")

        self.assertEqual(first_value, second_value)
        self.assertIn(first_value, AVATAR_BACKGROUND_PALETTE)


if __name__ == "__main__":
    unittest.main()
