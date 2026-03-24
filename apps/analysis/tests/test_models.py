"""Django-тесты моделей анализа."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.analysis.models import AnalysisResult, AnalysisRun
from apps.content.models import AnalysisPrompt, Game, Scenario, ScenarioPrompt
from apps.dialogs.models import DialogSession


class AnalysisModelsTests(TestCase):
    """Проверяет ключевые ограничения моделей ``analysis``.

    Параметры:
        Экземпляр класса создаётся Django test runner.

    Возвращает:
        Экземпляр ``TestCase``.

    Исключения:
        AssertionError: Возникает при расхождении с ожидаемыми инвариантами.

    Побочные эффекты:
        Создаёт тестовые записи в базе данных.
    """

    def setUp(self) -> None:
        """Подготавливает фикстуры диалога и аналитического критерия.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            Возможны стандартные ошибки ORM при создании фикстур.

        Побочные эффекты:
            Создаёт тестовые записи в базе данных.
        """
        self.user = User.objects.create_user(
            email="analysis-user@example.com",
            nickname="Аналитик",
            password="12345678",
        )
        self.game = Game.objects.create(slug="game-analysis", title="Игра", sort_order=1)
        self.scenario = Scenario.objects.create(
            game=self.game,
            slug="scenario-analysis",
            title="Сценарий",
            conditions_text="Условия",
            opening_message_text="Привет",
            sort_order=1,
        )
        self.scenario_prompt = ScenarioPrompt.objects.create(
            scenario=self.scenario,
            title="Промт",
            prompt_text="Игровой промт",
            is_active=True,
        )
        self.dialog = DialogSession.objects.create(
            user=self.user,
            game=self.game,
            scenario=self.scenario,
            scenario_prompt_used=self.scenario_prompt,
            status=DialogSession.Status.FINISHED,
            started_at=timezone.now(),
            ended_at=timezone.now(),
            ended_reason=DialogSession.EndedReason.MANUAL_FEEDBACK,
            user_message_count=1,
            assistant_message_count=1,
            effective_duration_seconds=600,
            effective_user_message_max_chars=2500,
            effective_game_reply_max_chars=2500,
            effective_analysis_reply_max_chars=5000,
            effective_llm_model_name="Qwen/Qwen3-32B",
            effective_llm_temperature=Decimal("0.70"),
            effective_llm_top_p=Decimal("0.80"),
            effective_llm_game_max_tokens=1024,
            effective_llm_analysis_max_tokens=1024,
            conditions_snapshot_text="Условия",
            opening_message_snapshot_text="Привет",
        )
        self.analysis_prompt = AnalysisPrompt.objects.create(
            game=self.game,
            alias="criterion-a",
            title="Критерий",
            header_text="Заголовок",
            prompt_text="Промт анализа",
            sort_order=1,
        )

    def test_analysis_run_skipped_requires_analysis_skipped_dialog(self) -> None:
        """Проверяет согласованность skipped-анализа со статусом диалога.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при несогласованном статусе.

        Побочные эффекты:
            Побочные эффекты отсутствуют.
        """
        run = AnalysisRun(
            dialog=self.dialog,
            status=AnalysisRun.Status.SKIPPED,
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            run.full_clean()

    def test_analysis_result_rejects_rating_out_of_range(self) -> None:
        """Проверяет защиту от рейтинга вне диапазона критерия.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            ValidationError: Ожидается при некорректном рейтинге.

        Побочные эффекты:
            Создаёт запуск анализа в базе данных.
        """
        run = AnalysisRun.objects.create(
            dialog=self.dialog,
            status=AnalysisRun.Status.COMPLETED,
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )
        result = AnalysisResult(
            analysis_run=run,
            analysis_prompt=self.analysis_prompt,
            sort_order_snapshot=1,
            alias_snapshot="criterion-a",
            title_snapshot="Критерий",
            header_snapshot_text="Заголовок",
            rating=6,
            rating_min=0,
            rating_max=5,
            analysis_text="Текст анализа",
        )

        with self.assertRaises(ValidationError):
            result.full_clean()

    def test_only_one_analysis_run_per_dialog_is_allowed(self) -> None:
        """Проверяет ограничение one-to-one между диалогом и анализом.

        Параметры:
            Явные параметры отсутствуют.

        Возвращает:
            ``None``.

        Исключения:
            IntegrityError: Ожидается при попытке создать второй запуск.

        Побочные эффекты:
            Создаёт тестовые записи запусков анализа в базе данных.
        """
        AnalysisRun.objects.create(
            dialog=self.dialog,
            status=AnalysisRun.Status.COMPLETED,
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )

        with self.assertRaises(IntegrityError):
            AnalysisRun.objects.create(
                dialog=self.dialog,
                status=AnalysisRun.Status.PENDING,
                started_at=timezone.now(),
            )
