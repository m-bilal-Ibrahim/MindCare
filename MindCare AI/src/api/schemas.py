"""Pydantic request and response contracts."""

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """Input features supplied to the recommendation endpoint."""

    features: dict[str, float] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    """Model recommendation response."""

    recommendation: str


class ChatRequest(BaseModel):
    """Input for the assistant endpoint."""

    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    """Assistant response."""

    message: str
