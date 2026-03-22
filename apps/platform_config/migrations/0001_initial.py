"""Начальная миграция приложения ``platform_config``."""

from __future__ import annotations

import decimal
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Создаёт глобальные настройки платформы и UI-тексты."""

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активная запись")),
                ("default_dialog_duration_minutes", models.PositiveSmallIntegerField(default=10, help_text="Глобальная длительность диалога по умолчанию.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Длительность диалога по умолчанию")),
                ("user_timer_min_minutes", models.PositiveSmallIntegerField(default=5, help_text="Нижняя граница будущей пользовательской настройки таймера.", verbose_name="Минимум пользовательского таймера")),
                ("user_timer_max_minutes", models.PositiveSmallIntegerField(default=20, help_text="Верхняя граница будущей пользовательской настройки таймера.", verbose_name="Максимум пользовательского таймера")),
                ("default_show_timer", models.BooleanField(default=True, verbose_name="Показывать таймер по умолчанию")),
                ("max_user_message_chars", models.PositiveIntegerField(default=2500, help_text="Серверный лимит длины пользовательского сообщения.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Лимит пользовательского сообщения")),
                ("max_game_reply_chars", models.PositiveIntegerField(default=2500, help_text="Лимит длины игрового ответа LLM.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Лимит игрового ответа")),
                ("max_analysis_reply_chars", models.PositiveIntegerField(default=5000, help_text="Лимит длины аналитического ответа LLM.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Лимит аналитического ответа")),
                ("llm_base_url", models.URLField(help_text="Базовый URL OpenAI-compatible/vLLM сервера.", verbose_name="LLM base URL")),
                ("llm_api_key", models.CharField(blank=True, help_text="Ключ доступа к LLM. Не должен выводиться в открытом виде во фронтенде и логах.", max_length=255, verbose_name="LLM API key")),
                ("llm_model_name", models.CharField(default="Qwen/Qwen3-32B", help_text="Имя модели LLM по умолчанию.", max_length=255, verbose_name="Имя модели LLM")),
                ("llm_temperature", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.70"), help_text="Температура генерации для LLM.", max_digits=3, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00")), django.core.validators.MaxValueValidator(decimal.Decimal("2.00"))], verbose_name="LLM temperature")),
                ("llm_top_p", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.80"), help_text="Параметр top_p для LLM.", max_digits=3, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00")), django.core.validators.MaxValueValidator(decimal.Decimal("1.00"))], verbose_name="LLM top_p")),
                ("llm_game_max_tokens", models.PositiveIntegerField(default=1024, help_text="Ограничение max_tokens для игрового режима.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Game max_tokens")),
                ("llm_analysis_max_tokens", models.PositiveIntegerField(default=1024, help_text="Ограничение max_tokens для аналитического режима.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Analysis max_tokens")),
                ("client_abort_grace_seconds", models.PositiveSmallIntegerField(default=5, help_text="Окно ожидания после клиентского разрыва соединения.", validators=[django.core.validators.MinValueValidator(1)], verbose_name="Ожидание после abort")),
            ],
            options={
                "verbose_name": "Настройки платформы",
                "verbose_name_plural": "Настройки платформы",
            },
        ),
        migrations.CreateModel(
            name="UIText",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("key", models.SlugField(unique=True, verbose_name="Ключ")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("text_value", models.TextField(verbose_name="Текст")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_ui_texts", to="accounts.user", verbose_name="Изменено пользователем")),
            ],
            options={
                "verbose_name": "UI-текст",
                "verbose_name_plural": "UI-тексты",
                "ordering": ["key"],
            },
        ),
        migrations.AddConstraint(
            model_name="platformsettings",
            constraint=models.UniqueConstraint(condition=models.Q(is_active=True), fields=("is_active",), name="platform_config_single_active_settings"),
        ),
    ]
