"""Сервисы приложения ``dialogs``."""

from .abandon_policy import DialogAbandonDecision, DialogAbandonDecisionService
from .finish_policy import DialogFinishDecision, DialogFinishDecisionService
from .llm_context import build_game_call_messages, render_analysis_transcript
from .message_dto import DialogMessageDTO, DialogMessageDTOBuilder
from .runtime_state import DialogRuntimeState, DialogRuntimeStateBuilder

__all__ = [
    "DialogAbandonDecision",
    "DialogAbandonDecisionService",
    "DialogFinishDecision",
    "DialogFinishDecisionService",
    "DialogMessageDTO",
    "DialogMessageDTOBuilder",
    "DialogRuntimeState",
    "DialogRuntimeStateBuilder",
    "build_game_call_messages",
    "render_analysis_transcript",
]
