"""Сервисы приложения ``dialogs``."""

from .abandon_policy import DialogAbandonDecision, DialogAbandonDecisionService
from .finish_policy import DialogFinishDecision, DialogFinishDecisionService
from .llm_context import build_game_call_messages, render_analysis_transcript
from .runtime_state import DialogRuntimeState, DialogRuntimeStateBuilder

__all__ = [
    "DialogAbandonDecision",
    "DialogAbandonDecisionService",
    "DialogFinishDecision",
    "DialogFinishDecisionService",
    "DialogRuntimeState",
    "DialogRuntimeStateBuilder",
    "build_game_call_messages",
    "render_analysis_transcript",
]
