"""Начальная миграция приложения ``content``."""

from __future__ import annotations

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """Создаёт базовые контентные модели игр, сценариев и промтов."""

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Game",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("short_description", models.TextField(blank=True, verbose_name="Краткое описание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок показа")),
                ("is_published", models.BooleanField(default=False, verbose_name="Опубликована")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_game_created_set", to="accounts.user", verbose_name="Создано пользователем")),
            ],
            options={
                "verbose_name": "Игра",
                "verbose_name_plural": "Игры",
                "ordering": ["sort_order", "title"],
                "indexes": [models.Index(fields=["is_published", "is_archived"], name="content_game_publish_arch_idx")],
            },
        ),
        migrations.CreateModel(
            name="ScenarioMediaAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("title", models.CharField(max_length=255, verbose_name="Название ресурса")),
                ("file", models.FileField(upload_to="scenario_media/", verbose_name="Файл")),
                ("original_filename", models.CharField(blank=True, max_length=255, verbose_name="Исходное имя файла")),
                ("mime_type", models.CharField(blank=True, max_length=255, verbose_name="MIME-тип")),
                ("file_size_bytes", models.BigIntegerField(blank=True, null=True, verbose_name="Размер файла в байтах")),
                ("checksum_sha256", models.CharField(blank=True, max_length=64, verbose_name="SHA256")),
                ("previous_version", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="next_versions", to="content.scenariomediaasset", verbose_name="Предыдущая версия")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="uploaded_media_assets", to="accounts.user", verbose_name="Загрузил пользователь")),
            ],
            options={
                "verbose_name": "Медиа-ресурс сценария",
                "verbose_name_plural": "Медиа-ресурсы сценариев",
                "ordering": ["title", "created_at"],
                "indexes": [models.Index(fields=["is_archived", "created_at"], name="content_media_arch_created_idx")],
            },
        ),
        migrations.CreateModel(
            name="SystemPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("key", models.SlugField(verbose_name="Ключ")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("prompt_text", models.TextField(verbose_name="Текст системного промта")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_systemprompt_created_set", to="accounts.user", verbose_name="Создано пользователем")),
            ],
            options={
                "verbose_name": "Системный промт",
                "verbose_name_plural": "Системные промты",
                "ordering": ["key", "-created_at"],
                "indexes": [models.Index(fields=["key", "is_active"], name="content_system_prompt_key_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="Scenario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("slug", models.SlugField(verbose_name="Slug")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("short_description", models.TextField(blank=True, verbose_name="Краткое описание")),
                ("conditions_text", models.TextField(verbose_name="Текст условий")),
                ("opening_message_text", models.TextField(verbose_name="Стартовая реплика")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок показа")),
                ("is_published", models.BooleanField(default=False, verbose_name="Опубликован")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_scenario_created_set", to="accounts.user", verbose_name="Создано пользователем")),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scenarios", to="content.game", verbose_name="Игра")),
                ("media_asset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="scenarios", to="content.scenariomediaasset", verbose_name="Медиа-ресурс")),
            ],
            options={
                "verbose_name": "Сценарий",
                "verbose_name_plural": "Сценарии",
                "ordering": ["game__sort_order", "sort_order", "title"],
                "indexes": [
                    models.Index(fields=["game", "sort_order"], name="content_scenario_game_sort_idx"),
                    models.Index(fields=["is_published", "is_archived"], name="content_scenario_publish_arch_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AnalysisPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("alias", models.SlugField(verbose_name="Alias")),
                ("title", models.CharField(max_length=255, verbose_name="Название критерия")),
                ("header_text", models.CharField(max_length=255, verbose_name="Заголовок карточки")),
                ("comment_text", models.TextField(blank=True, verbose_name="Комментарий для админки")),
                ("prompt_text", models.TextField(verbose_name="Текст аналитического промта")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок запуска")),
                ("min_rating", models.SmallIntegerField(default=0, verbose_name="Минимальный балл")),
                ("max_rating", models.SmallIntegerField(default=5, verbose_name="Максимальный балл")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_analysisprompt_created_set", to="accounts.user", verbose_name="Создано пользователем")),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analysis_prompts", to="content.game", verbose_name="Игра")),
            ],
            options={
                "verbose_name": "Аналитический промт",
                "verbose_name_plural": "Аналитические промты",
                "ordering": ["game", "sort_order", "title"],
                "indexes": [models.Index(fields=["game", "sort_order", "is_active"], name="content_analysis_prompt_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="ScenarioPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирована")),
                ("archived_at", models.DateTimeField(blank=True, null=True, verbose_name="Архивирована в")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("title", models.CharField(max_length=255, verbose_name="Название версии")),
                ("prompt_text", models.TextField(verbose_name="Текст промта")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_scenarioprompt_created_set", to="accounts.user", verbose_name="Создано пользователем")),
                ("scenario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scenario_prompts", to="content.scenario", verbose_name="Сценарий")),
            ],
            options={
                "verbose_name": "Игровой промт",
                "verbose_name_plural": "Игровые промты",
                "ordering": ["scenario", "-created_at"],
                "indexes": [models.Index(fields=["scenario", "is_active"], name="content_scenario_prompt_active_idx")],
            },
        ),
        migrations.AddConstraint(
            model_name="systemprompt",
            constraint=models.UniqueConstraint(condition=models.Q(is_active=True), fields=("key",), name="content_system_prompt_single_active_per_key"),
        ),
        migrations.AddConstraint(
            model_name="scenario",
            constraint=models.UniqueConstraint(fields=("game", "slug"), name="content_scenario_unique_game_slug"),
        ),
        migrations.AddConstraint(
            model_name="analysisprompt",
            constraint=models.UniqueConstraint(fields=("game", "alias"), name="content_analysis_prompt_unique_alias"),
        ),
        migrations.AddConstraint(
            model_name="analysisprompt",
            constraint=models.UniqueConstraint(fields=("game", "sort_order"), name="content_analysis_prompt_unique_sort_order"),
        ),
        migrations.AddConstraint(
            model_name="analysisprompt",
            constraint=models.CheckConstraint(check=models.Q(min_rating__lte=models.F("max_rating")), name="content_analysis_prompt_valid_rating_range"),
        ),
        migrations.AddConstraint(
            model_name="scenarioprompt",
            constraint=models.UniqueConstraint(condition=models.Q(is_active=True), fields=("scenario",), name="content_scenario_prompt_single_active_per_scenario"),
        ),
    ]
