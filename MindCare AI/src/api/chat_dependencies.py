"""Composition-root dependencies for chat workflows."""

from src.application.chat import ChatAssistant


def get_chat_assistant() -> ChatAssistant:
    """Build the chat application service."""
    return ChatAssistant()