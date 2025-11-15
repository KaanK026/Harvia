import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Request

from backend.src.core.core_firebase_admin import db
from backend.src.models.error_models import generic_fail
from backend.src.models.request_models import StartSessionRequest, StopSessionRequest, SaunaRecommendationRequest
from backend.src.models.response_models import StartSessionResponse, StopSessionResponse, SaunaRecommendationResponse
from backend.src.services.recommendation import get_sauna_engine
from backend.src.utils.logger import get_logger

logger = get_logger("sauna-backend.sauna")
router = APIRouter()


@router.get("/recommendations", response_model=SaunaRecommendationResponse)
def get_sauna_recommendations(
        request: Request,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        height: Optional[float] = None,
        weight: Optional[float] = None,
        goals: Optional[List[str]] = None
) -> SaunaRecommendationResponse:
    """
    Get optimal sauna settings recommendations for a user.
    If user_id is provided, fetches profile data from Firestore.
    Otherwise, uses provided parameters.
    """
    sauna_engine = get_sauna_engine()
    if sauna_engine is None:
        raise generic_fail("Sauna recommendation engine is not initialized.")

    uid = request.state.uid


    # Try to fetch user profile from Firestore if parameters are not provided
    if db and (age is None or gender is None or height is None or weight is None or goals is None):
        try:
            user_ref = db.collection('users').document(uid)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                age = age or user_data.get('age')
                gender = gender or user_data.get('gender', 'Prefer not to say')
                height = height or user_data.get('height')  # Should be in meters
                weight = weight or user_data.get('weight')  # Should be in kg
                goals = goals or user_data.get('goals', [])

                logger.info(f"Fetched user profile from Firestore for user {uid}")
            else:
                logger.warning(f"User profile not found in Firestore for user {uid}")
        except Exception as e:
            logger.error(f"Error fetching user profile from Firestore: {e}")

    # Validate required parameters
    if age is None or height is None or weight is None:
        raise generic_fail(
            "Age, height, and weight must be provided either as parameters or in the user profile."
        )

    if goals is None or len(goals) == 0:
        raise generic_fail(
            detail="At least one goal must be provided."
        )

    # Ensure height is in meters (convert from cm if needed)
    if height > 3:  # Likely in cm, convert to meters
        height = height / 100
        logger.info(f"Converted height from cm to meters: {height}m")

    # Default gender if not provided
    if gender is None:
        gender = "Prefer not to say"

    try:
        # Get recommendations from neural network
        recommendation = sauna_engine.predict(
            age=float(age),
            gender=gender,
            height=float(height),
            weight=float(weight),
            selected_goals=goals
        )

        logger.info(f"Generated recommendations for user {uid}: {recommendation}")

        return SaunaRecommendationResponse(
            temperature=recommendation['temperature'],
            humidity=recommendation['humidity'],
            session_length=recommendation['session_length'],
            user_id=uid,
            goals_used=goals
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise generic_fail(
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.post("/recommendations", response_model=SaunaRecommendationResponse)
def get_sauna_recommendations_post(
    request: Request,
    payload: SaunaRecommendationRequest,
) -> SaunaRecommendationResponse:
    """
    Get optimal sauna settings recommendations for a user (POST version).
    Accepts user data in request body.
    """
    return get_sauna_recommendations(
        request,
        age=payload.age,
        gender=payload.gender,
        height=payload.height,
        weight=payload.weight,
        goals=payload.goals
    )