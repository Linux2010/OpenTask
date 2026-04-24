"""
API Key Authentication Utility

Verify X-Bot-Key header for API authentication.
"""

from fastapi import HTTPException, Header
from app.config import settings


async def verify_api_key(x_bot_key: str = Header(None, alias="X-Bot-Key")):
    """Verify API Key from header"""
    if not x_bot_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Bot-Key header"
        )
    
    if x_bot_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    
    return x_bot_key