"""Recommendation endpoint."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_recommendation_use_case
from src.api.schemas import RecommendationRequest, RecommendationResponse
from src.application.recommend import RecommendUser

router = APIRouter(prefix="/recommend", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest,
    use_case: RecommendUser = Depends(get_recommendation_use_case),
) -> RecommendationResponse:
    """Translate the HTTP request into the recommendation use case."""
    return RecommendationResponse(recommendation=use_case.execute(request.features))
