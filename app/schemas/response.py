"""
Response Models

Common response models for API.
"""

from pydantic import BaseModel
from typing import Optional, Any


class ResponseModel(BaseModel):
    """Standard response model"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None