"""Тесты OpenAI-compatible интеграции LLM."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from apps.integrations.services import (
    LLMConfigurationError,
    LLMEmptyResponseError,
    LLMMessage,
    LLMMode,
    LLMTemporaryError,
    OpenAICompatibleLLMClient,
    build_platform_llm_settings_snapshot,
    build_request_from_platform_settings,
    get_active_platform_llm_settings,
)


class LLMMessageTests(TestCase):
    """Проверяет базовую валидацию объектов сообщений LLM."""

    def test_message_rejects_empty_content(self) -> None:
        """Проверяет запрет пустого текста для payload к модели.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        with self.assertRaises(ValueError):
            LLMMessage(role="user", content="   ")

    def test_message_rejects_unknown_role(self) -> None:
        """Проверяет запрет неподдерживаемой роли chat completion.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        with self.assertRaises(ValueError):
            LLMMessage(role="tool", content="ok")


class OpenAICompatibleLLMClientTests(TestCase):
    """Проверяет адаптер OpenAI-compatible/vLLM вызовов."""

    def test_generate_reply_returns_normalized_response(self) -> None:
        """Проверяет успешную нормализацию ответа провайдера.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются тестом при несоответствии ожиданиям.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        response = SimpleNamespace(
            id="req-123",
            model="Qwen/Qwen3-32B",
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=15, total_tokens=25),
            choices=[SimpleNamespace(message=SimpleNamespace(content="  Готовый ответ  "))],
        )
        completions = SimpleNamespace(create=Mock(return_value=response))
        client_instance = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        client_factory = Mock(return_value=client_instance)
        client = OpenAICompatibleLLMClient(client_factory=client_factory)

        request = build_request_from_platform_settings(
            mode=LLMMode.GAME,
            settings_snapshot=build_platform_llm_settings_snapshot(
                settings=self._build_settings_object(),
                mode=LLMMode.GAME,
            ),
            messages=[
                LLMMessage(role="system", content="Вы — персонаж."),
                LLMMessage(role="user", content="Привет"),
            ],
        )

        result = client.generate_reply(request)

        client_factory.assert_called_once_with(base_url="https://llm.example.com/v1", api_key="secret")
        completions.create.assert_called_once_with(
            model="Qwen/Qwen3-32B",
            messages=[
                {"role": "system", "content": "Вы — персонаж."},
                {"role": "user", "content": "Привет"},
            ],
            max_tokens=512,
            temperature=0.7,
            top_p=0.8,
        )
        self.assertEqual(result.reply_text, "Готовый ответ")
        self.assertEqual(result.provider_request_id, "req-123")
        self.assertEqual(result.raw_provider_payload["usage"]["total_tokens"], 25)

    def test_generate_reply_raises_empty_response_error_for_blank_content(self) -> None:
        """Проверяет обработку пустого текстового ответа от провайдера.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="   "))])
        completions = SimpleNamespace(create=Mock(return_value=response))
        client_instance = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        client = OpenAICompatibleLLMClient(client_factory=Mock(return_value=client_instance))
        request = build_request_from_platform_settings(
            mode=LLMMode.ANALYSIS,
            settings_snapshot=build_platform_llm_settings_snapshot(
                settings=self._build_settings_object(),
                mode=LLMMode.ANALYSIS,
            ),
            messages=[LLMMessage(role="system", content="Проанализируй диалог.")],
        )

        with self.assertRaises(LLMEmptyResponseError):
            client.generate_reply(request)

    def test_generate_reply_normalizes_provider_exception(self) -> None:
        """Проверяет нормализацию внешней SDK-ошибки в доменный тип.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        completions = SimpleNamespace(create=Mock(side_effect=RuntimeError("timeout")))
        client_instance = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        client = OpenAICompatibleLLMClient(client_factory=Mock(return_value=client_instance))
        request = build_request_from_platform_settings(
            mode=LLMMode.GAME,
            settings_snapshot=build_platform_llm_settings_snapshot(
                settings=self._build_settings_object(),
                mode=LLMMode.GAME,
            ),
            messages=[LLMMessage(role="user", content="Привет")],
        )

        with self.assertRaises(LLMTemporaryError):
            client.generate_reply(request)

    def _build_settings_object(self) -> SimpleNamespace:
        """Создаёт тестовый объект настроек без зависимости от Django ORM.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            Объект с полями, совместимыми с ``PlatformSettingsLike``.

        Исключения:
            Специальные исключения не генерируются.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        return SimpleNamespace(
            llm_base_url="https://llm.example.com/v1",
            llm_api_key="secret",
            llm_model_name="Qwen/Qwen3-32B",
            llm_temperature=Decimal("0.70"),
            llm_top_p=Decimal("0.80"),
            llm_game_max_tokens=512,
            llm_analysis_max_tokens=256,
            max_user_message_chars=2500,
            max_game_reply_chars=2000,
            max_analysis_reply_chars=5000,
        )


class PlatformLLMSettingsSnapshotTests(TestCase):
    """Проверяет чтение и преобразование LLM-настроек в DTO."""

    def test_snapshot_uses_game_tokens_for_game_mode(self) -> None:
        """Проверяет выбор игрового лимита ``max_tokens``.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        snapshot = build_platform_llm_settings_snapshot(
            settings=SimpleNamespace(
                llm_base_url="https://llm.example.com/v1",
                llm_api_key="",
                llm_model_name="Qwen/Qwen3-32B",
                llm_temperature=Decimal("0.70"),
                llm_top_p=Decimal("0.80"),
                llm_game_max_tokens=333,
                llm_analysis_max_tokens=777,
                max_user_message_chars=2500,
                max_game_reply_chars=2000,
                max_analysis_reply_chars=5000,
            ),
            mode=LLMMode.GAME,
        )

        self.assertEqual(snapshot.max_tokens, 333)
        self.assertEqual(snapshot.max_user_message_chars, 2500)

    def test_get_active_platform_llm_settings_uses_loader(self) -> None:
        """Проверяет чтение настроек через подменяемый loader.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        snapshot = get_active_platform_llm_settings(
            mode=LLMMode.ANALYSIS,
            settings_loader=lambda: SimpleNamespace(
                llm_base_url="https://llm.example.com/v1",
                llm_api_key="api-key",
                llm_model_name="Qwen/Qwen3-32B",
                llm_temperature=Decimal("0.70"),
                llm_top_p=Decimal("0.80"),
                llm_game_max_tokens=500,
                llm_analysis_max_tokens=900,
                max_user_message_chars=2500,
                max_game_reply_chars=2000,
                max_analysis_reply_chars=5000,
            ),
        )

        self.assertEqual(snapshot.max_tokens, 900)
        self.assertEqual(snapshot.api_key, "api-key")

    def test_get_active_platform_llm_settings_raises_when_loader_fails(self) -> None:
        """Проверяет контролируемую ошибку при сбое чтения настроек.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Исключения перехватываются самим тестом.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        with self.assertRaises(LLMConfigurationError):
            get_active_platform_llm_settings(
                mode=LLMMode.GAME,
                settings_loader=lambda: (_ for _ in ()).throw(RuntimeError("db unavailable")),
            )
