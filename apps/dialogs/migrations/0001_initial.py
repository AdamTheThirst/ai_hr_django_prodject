"""Начальная миграция приложения ``dialogs``."""

from __future__ import annotations

import decimal
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """Создаёт модели игровых сессий и сообщений диалога."""

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DialogSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("status", models.CharField(choices=[("active", "Активный"), ("finished", "Завершён"), ("aborted", "Прерван"), ("analysis_skipped", "Анализ пропущен")], default="active", max_length=32, verbose_name="Статус")),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Начат")),
                ("ended_at", models.DateTimeField(blank=True, null=True, verbose_name="Завершён")),
                ("ended_reason", models.CharField(blank=True, choices=[("manual_feedback", "Ручное завершение"), ("timeout", "Таймаут"), ("page_leave", "Уход со страницы"), ("inactive_timeout", "Таймаут неактивности"), ("no_user_messages", "Нет пользовательских реплик")], max_length=32, verbose_name="Причина завершения")),
                ("user_message_count", models.PositiveIntegerField(default=0, verbose_name="Количество сообщений пользователя")),
                ("assistant_message_count", models.PositiveIntegerField(default=0, verbose_name="Количество сообщений ИИ")),
                ("effective_duration_seconds", models.PositiveIntegerField(verbose_name="Зафиксированная длительность в секундах")),
                ("effective_user_message_max_chars", models.PositiveIntegerField(verbose_name="Зафиксированный лимит пользовательского сообщения")),
                ("effective_game_reply_max_chars", models.PositiveIntegerField(verbose_name="Зафиксированный лимит игрового ответа")),
                ("effective_analysis_reply_max_chars", models.PositiveIntegerField(verbose_name="Зафиксированный лимит аналитического ответа")),
                ("effective_llm_model_name", models.CharField(max_length=255, verbose_name="Зафиксированное имя модели")),
                ("effective_llm_temperature", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.70"), max_digits=3, verbose_name="Зафиксированная temperature")),
                ("effective_llm_top_p", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.80"), max_digits=3, verbose_name="Зафиксированный top_p")),
                ("effective_llm_game_max_tokens", models.PositiveIntegerField(verbose_name="Зафиксированный game max_tokens")),
                ("effective_llm_analysis_max_tokens", models.PositiveIntegerField(verbose_name="Зафиксированный analysis max_tokens")),
                ("conditions_snapshot_text", models.TextField(verbose_name="Snapshot условий")),
                ("opening_message_snapshot_text", models.TextField(verbose_name="Snapshot стартовой реплики")),
                ("last_client_activity_at", models.DateTimeField(blank=True, null=True, verbose_name="Последняя активность клиента")),
                ("client_aborted_at", models.DateTimeField(blank=True, null=True, verbose_name="Сигнал client abort")),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dialog_sessions", to="content.game", verbose_name="Игра")),
                ("scenario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dialog_sessions", to="content.scenario", verbose_name="Сценарий")),
                ("scenario_prompt_used", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dialog_sessions", to="content.scenarioprompt", verbose_name="Использованный игровой промт")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dialog_sessions", to="accounts.user", verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Игровая сессия",
                "verbose_name_plural": "Игровые сессии",
                "ordering": ["-started_at"],
                "indexes": [
                    models.Index(fields=["user", "status"], name="dialogs_session_user_status_idx"),
                    models.Index(fields=["game"], name="dialogs_session_game_idx"),
                    models.Index(fields=["scenario"], name="dialogs_session_scenario_idx"),
                    models.Index(fields=["started_at"], name="dialogs_session_started_at_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="DialogMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence_no", models.PositiveIntegerField(verbose_name="Порядковый номер")),
                ("role", models.CharField(choices=[("assistant", "Ассистент"), ("user", "Пользователь")], max_length=16, verbose_name="Роль")),
                ("text", models.TextField(verbose_name="Текст")),
                ("char_count", models.PositiveIntegerField(verbose_name="Количество символов")),
                ("llm_request_id", models.CharField(blank=True, max_length=255, verbose_name="Идентификатор LLM-запроса")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("dialog", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="dialogs.dialogsession", verbose_name="Диалог")),
            ],
            options={
                "verbose_name": "Сообщение диалога",
                "verbose_name_plural": "Сообщения диалога",
                "ordering": ["dialog", "sequence_no"],
                "indexes": [models.Index(fields=["dialog", "sequence_no"], name="dialogs_message_dialog_sequence_idx")],
            },
        ),
        migrations.AddConstraint(
            model_name="dialogsession",
            constraint=models.UniqueConstraint(condition=models.Q(status="active"), fields=("user",), name="dialogs_single_active_dialog_per_user"),
        ),
        migrations.AddConstraint(
            model_name="dialogmessage",
            constraint=models.UniqueConstraint(fields=("dialog", "sequence_no"), name="dialogs_message_unique_sequence"),
        ),
    ]
