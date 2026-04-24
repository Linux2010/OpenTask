"""
Task Pydantic Schemas

Request and response models for task API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    """Task creation request"""
    task_name: str = Field(..., max_length=100, description="Task name")
    task_description: Optional[str] = Field(None, description="Task description")
    task_params: Optional[str] = Field(None, description="Task parameters (JSON)")
    assigned_to: str = Field(..., max_length=50, description="Assigned bot")
    priority: str = Field(default="P2", description="Priority (P0/P1/P2)")
    created_by: str = Field(default="hope", description="Creator")


class TaskUpdate(BaseModel):
    """Task update request"""
    task_name: Optional[str] = Field(None, max_length=100)
    task_description: Optional[str] = None
    task_params: Optional[str] = None
    assigned_to: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)


class TaskResponse(BaseModel):
    """Task response model"""
    id: int
    task_name: str
    task_description: Optional[str] = None
    task_params: Optional[str] = None
    assigned_to: str
    priority: str
    status: str
    progress: Optional[int] = 0
    created_time: datetime
    started_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = 0
    created_by: Optional[str] = None


class TaskComplete(BaseModel):
    """Task complete request"""
    result: str = Field(..., description="Execution result")


class TaskFail(BaseModel):
    """Task fail request"""
    error_message: str = Field(..., description="Error message")