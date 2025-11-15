import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Request

from backend.src.models.error_models import generic_fail
from backend.src.models.request_models import StartSessionRequest, StopSessionRequest, SaunaRecommendationRequest
from backend.src.models.response_models import StartSessionResponse, StopSessionResponse, SaunaRecommendationResponse
from backend.src.services.recommendation import get_sauna_engine
from backend.src.utils.logger import get_logger

logger = get_logger("sauna-backend.sauna")
router = APIRouter()
#TODO: FIX



# Keep your existing response model
# from your code: SaunaRecommendationResponse

@router.post("/recommendations", response_model=SaunaRecommendationResponse)
def post_sauna_recommendations(request: SaunaRecommendationRequest):
    age = request.age
    gender = request.gender
    height = request.height
    weight = request.weight
    goals = request.goals
    print(goals)
    """
    Get optimal sauna settings recommendations for a user.
    If user_id is provided, fetches profile data from Firestore.
    Otherwise, uses provided parameters.
    """
    sauna_engine = get_sauna_engine()
    if sauna_engine is None:
        raise generic_fail("Sauna recommendation engine is not initialized.")



    # Ensure height is in meters (convert from cm if needed)
    if height > 3:  # Likely in cm, convert to meters
        height = height / 100
        logger.info(f"Converted height from cm to meters: {height}m")


    try:
        # Get recommendations from neural network
        recommendation = sauna_engine.predict(
            age=float(age),
            gender=gender,
            height=float(height),
            weight=float(weight),
            selected_goals=goals
        )



        return SaunaRecommendationResponse(
            temperature=recommendation['temperature'],
            humidity=recommendation['humidity'],
            session_length=recommendation['session_length'],
            goals_used=goals
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise generic_fail(
            detail=f"Error generating recommendations: {str(e)}"
        )

