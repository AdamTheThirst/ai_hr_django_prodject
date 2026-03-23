"""Сервисы приложения ``dialogs``."""

from .llm_context import build_game_call_messages, render_analysis_transcript

__all__ = [
    "build_game_call_messages",
    "render_analysis_transcript",
]
