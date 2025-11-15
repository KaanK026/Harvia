from fastapi import APIRouter, Request

from backend.src.models.response_models import FriendsResponse, Friend

router = APIRouter()

@router.get("/friends", response_model=FriendsResponse)
def list_friends(request: Request) -> FriendsResponse:
    sample = [
        Friend(id="friend_1", name="Alex", status="online"),
        Friend(id="friend_2", name="Sam", status="offline"),
        Friend(id="friend_3", name="Taylor", status="sauna"),
    ]
    return FriendsResponse(friends=sample)
