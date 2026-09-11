"""Recommendation endpoint."""

from fastapi import APIRouter

from src.api.schemas import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/recommend", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """Return a placeholder until the approved model is registered."""
    return RecommendationResponse(recommendation="review_required")
