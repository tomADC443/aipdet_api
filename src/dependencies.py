from fastapi import HTTPException, Request
from jwt import ExpiredSignatureError, InvalidTokenError
from functools import wraps

import jwt
from src.config import get_settings

settings = get_settings()


def decode_jwt(token: str):
    # Token expiration check is done automatically by the JWT library
    try:
        payload = jwt.decode(token, settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        return payload  # Contains user information (e.g., "sub", "email")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(request: Request):
    token = request.cookies.get("auth_token")  # Read the token from the cookie
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_data = decode_jwt(token)  # Decode and validate the JWT
    return user_data  # Return user info (e.g., "sub", "email")


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Assume `get_current_user` is injected elsewhere
        if not kwargs.get('current_user'):
            raise HTTPException(
                status_code=401, detail="Authentication required")
        return func(*args, **kwargs)
    return wrapper
