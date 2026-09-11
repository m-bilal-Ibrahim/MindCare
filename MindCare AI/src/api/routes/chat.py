"""Chat assistant endpoint."""

from fastapi import APIRouter

from src.api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Return a bounded placeholder response for the assistant contract."""
    return ChatResponse(message="Please consult a qualified mental-health professional.")
