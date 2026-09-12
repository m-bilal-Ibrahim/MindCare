"""Chat assistant endpoint."""

from fastapi import APIRouter, Depends

from src.api.chat_dependencies import get_chat_assistant
from src.api.schemas import ChatRequest, ChatResponse
from src.application.chat import ChatAssistant

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    assistant: ChatAssistant = Depends(get_chat_assistant),
) -> ChatResponse:
    """Translate the HTTP request into the chat application service."""
    return ChatResponse(message=assistant.respond(request.message))
