"""
WebSocket authentication helpers.
"""
from __future__ import annotations

from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi import WebSocket

from engine.auth import TokenData, ALGORITHM, SECRET_KEY


def _extract_bearer_token(raw: str | None) -> str | None:
    if not raw:
        return None
    if not raw.lower().startswith("bearer "):
        return None
    token = raw.split(" ", 1)[1].strip()
    return token or None


async def authenticate_websocket(websocket: WebSocket) -> TokenData:
    """
    Authenticate a websocket via query token or Authorization header.

    Priority:
    1) query param: token
    2) Authorization: Bearer <token>
    """
    token = websocket.query_params.get("token")
    if not token:
        token = _extract_bearer_token(websocket.headers.get("authorization"))

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing websocket token",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        email: str | None = payload.get("email")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid websocket token",
            )
        return TokenData(user_id=user_id, email=email)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired websocket token",
        ) from exc
