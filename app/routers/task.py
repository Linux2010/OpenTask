"""
Task API Router

FastAPI routes for task management.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService
from app.utils.auth import verify_api_key

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get task list with filters"""
    return await TaskService.list_tasks(assigned_to, status, priority)


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new task"""
    return await TaskService.create_task(task)


@router.get("/tasks/pending", response_model=List[TaskResponse])
async def get_pending_tasks(
    assigned_to: str,
    api_key: str = Depends(verify_api_key)
):
    """Get pending tasks for a specific bot"""
    return await TaskService.get_pending_tasks(assigned_to)


@router.get("/tasks/{id}", response_model=TaskResponse)
async def get_task(
    id: int,
    api_key: str = Depends(verify_api_key)
):
    """Get task by ID"""
    task = await TaskService.get_task(id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{id}", response_model=TaskResponse)
async def update_task(
    id: int,
    task: TaskUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update task"""
    return await TaskService.update_task(id, task)


@router.delete("/tasks/{id}")
async def delete_task(
    id: int,
    api_key: str = Depends(verify_api_key)
):
    """Delete task (soft delete)"""
    return await TaskService.delete_task(id)


@router.put("/tasks/{id}/start", response_model=TaskResponse)
async def start_task(
    id: int,
    api_key: str = Depends(verify_api_key)
):
    """Start task execution"""
    return await TaskService.start_task(id)


@router.put("/tasks/{id}/complete", response_model=TaskResponse)
async def complete_task(
    id: int,
    result: str,
    api_key: str = Depends(verify_api_key)
):
    """Mark task as completed"""
    return await TaskService.complete_task(id, result)


@router.put("/tasks/{id}/fail", response_model=TaskResponse)
async def fail_task(
    id: int,
    error_message: str,
    api_key: str = Depends(verify_api_key)
):
    """Mark task as failed"""
    return await TaskService.fail_task(id, error_message)


@router.put("/tasks/{id}/retry", response_model=TaskResponse)
async def retry_task(
    id: int,
    api_key: str = Depends(verify_api_key)
):
    """Retry failed task"""
    return await TaskService.retry_task(id)


@router.put("/tasks/{id}/cancel", response_model=TaskResponse)
async def cancel_task(
    id: int,
    api_key: str = Depends(verify_api_key)
):
    """Cancel task"""
    return await TaskService.cancel_task(id)


@router.get("/stats/today")
async def get_today_stats(
    api_key: str = Depends(verify_api_key)
):
    """Get today's task statistics"""
    return await TaskService.get_today_stats()


@router.get("/logs/{task_id}")
async def get_task_logs(
    task_id: int,
    api_key: str = Depends(verify_api_key)
):
    """Get task logs"""
    return await TaskService.get_task_logs(task_id)