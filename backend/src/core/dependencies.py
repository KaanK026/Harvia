from fastapi import Request, HTTPException, status

def get_current_user_uid(request: Request) -> str:
    """
    Dependency to get the user UID from the request state,
    which is set by the FirebaseAuthMiddleware.
    """
    uid = getattr(request.state, "uid", None)
    if not uid:
        # This should ideally not be reached if middleware is applied correctly
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return uid