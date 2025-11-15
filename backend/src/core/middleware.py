from typing import Optional
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from firebase_admin import auth as fb_auth

from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


def _verify_firebase_user(authorization: Optional[str]) -> Optional[str]:
    """Helper to verify a Firebase ID token from the Authorization header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        decoded = fb_auth.verify_id_token(token)
        return decoded.get("uid")
    except Exception as e:
        logger.warning("Firebase token verification failed: %s", e)
        return None


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce Firebase authentication on protected routes."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        public_paths = ["/", "/health"]
        if request.url.path in public_paths:
            return await call_next(request)

        uid = _verify_firebase_user(request.headers.get("Authorization"))
        if not uid:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "User authentication required"}
            )

        request.state.uid = uid
        return await call_next(request)


async def log_requests(request: Request, call_next):
    """Middleware to log incoming requests and outgoing responses."""
    logger.info("REQ %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("RES %s %s -> %s", request.method, request.url.path, response.status_code)
    return response