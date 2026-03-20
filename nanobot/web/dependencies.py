"""Dependencies for web channel API."""

from fastapi import Request, WebSocket, HTTPException, status
from typing import Optional

from nanobot.config import get_config

config = get_config()


async def get_current_user(request: Request) -> str:
    """Get current user ID from query parameters."""
    empId = request.query_params.get("empId")
    if not empId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing empId parameter",
        )

    # Validate user permissions
    allow_list = config.channels.web.allow_from
    if not allow_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if "*" not in allow_list and empId not in allow_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return empId


async def get_current_user_ws(websocket: WebSocket) -> Optional[str]:
    """Get current user ID from WebSocket query parameters."""
    empId = websocket.query_params.get("empId")
    if not empId:
        return None

    # Validate user permissions
    allow_list = config.channels.web.allow_from
    if not allow_list:
        return None

    if "*" not in allow_list and empId not in allow_list:
        return None

    return empId
