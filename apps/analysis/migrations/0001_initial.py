"""Начальная миграция приложения ``analysis``."""

from __future__ import annotations

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """Создаёт модели запуска анализа и результатов по критериям."""

    initial = True

    dependencies = [
        ("content", "0001_initial"),
        ("dialogs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("status", models.CharField(choices=[("pending", "В очереди"), ("running", "Выполняется"), ("completed", "Завершён"), ("failed", "Ошибка"), ("skipped", "Пропущен")], default="pending", max_length=16, verbose_name="Статус")),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Запущен")),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="Завершён")),
                ("llm_attempt_count", models.PositiveIntegerField(default=0, verbose_name="Количество LLM-вызовов")),
                ("error_code", models.CharField(blank=True, max_length=255, verbose_name="Код ошибки")),
                ("error_message", models.TextField(blank=True, verbose_name="Описание ошибки")),
                ("dialog", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="analysis_run", to="dialogs.dialogsession", verbose_name="Диалог")),
            ],
            options={
                "verbose_name": "Запуск анализа",
                "verbose_name_plural": "Запуски анализа",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("sort_order_snapshot", models.PositiveIntegerField(verbose_name="Snapshot порядка")),
                ("alias_snapshot", models.SlugField(verbose_name="Snapshot alias")),
                ("title_snapshot", models.CharField(max_length=255, verbose_name="Snapshot названия")),
                ("header_snapshot_text", models.CharField(max_length=255, verbose_name="Snapshot заголовка")),
                ("comment_snapshot_text", models.TextField(blank=True, verbose_name="Snapshot комментария")),
                ("rating", models.SmallIntegerField(verbose_name="Рейтинг")),
                ("rating_min", models.SmallIntegerField(verbose_name="Минимум рейтинга")),
                ("rating_max", models.SmallIntegerField(verbose_name="Максимум рейтинга")),
                ("analysis_text", models.TextField(verbose_name="Текст анализа")),
                ("raw_llm_response_text", models.TextField(blank=True, verbose_name="Сырой ответ LLM")),
                ("parsed_json_snapshot", models.JSONField(blank=True, null=True, verbose_name="Snapshot валидного JSON")),
                ("validation_status", models.CharField(choices=[("valid", "Валиден"), ("invalid_json", "Невалидный JSON"), ("invalid_schema", "Невалидная схема"), ("fallback_saved", "Сохранён fallback")], default="valid", max_length=20, verbose_name="Статус валидации")),
                ("validation_error_message", models.TextField(blank=True, verbose_name="Ошибка валидации")),
                ("llm_attempt_count", models.PositiveIntegerField(default=1, verbose_name="Количество попыток LLM")),
                ("analysis_prompt", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="analysis_results", to="content.analysisprompt", verbose_name="Аналитический промт")),
                ("analysis_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="analysis.analysisrun", verbose_name="Запуск анализа")),
            ],
            options={
                "verbose_name": "Результат анализа",
                "verbose_name_plural": "Результаты анализа",
                "ordering": ["analysis_run", "sort_order_snapshot", "id"],
                "indexes": [models.Index(fields=["analysis_run", "sort_order_snapshot"], name="analysis_result_run_sort_idx")],
            },
        ),
        migrations.AddConstraint(
            model_name="analysisresult",
            constraint=models.UniqueConstraint(fields=("analysis_run", "analysis_prompt"), name="analysis_result_unique_prompt_per_run"),
        ),
    ]
