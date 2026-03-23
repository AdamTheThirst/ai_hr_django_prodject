"""Сервисы приложения ``dialogs``."""

from .finish_policy import DialogFinishDecision, DialogFinishDecisionService
from .llm_context import build_game_call_messages, render_analysis_transcript

__all__ = [
    "DialogFinishDecision",
    "DialogFinishDecisionService",
    "build_game_call_messages",
    "render_analysis_transcript",
]
