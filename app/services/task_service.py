"""
Task Service

Business logic for task management with real database operations.
"""

from typing import Optional, List
from datetime import datetime
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.utils.db import get_db_connection, execute_query, execute_insert, execute_update


def add_task_log(task_id: int, action: str, old_status: str, new_status: str, message: str = None):
    """记录任务状态变更日志到 bot_task_log 表"""
    sql = """
        INSERT INTO bot_task_log (task_id, action, old_status, new_status, message, operator, created_time)
        VALUES (%s, %s, %s, %s, %s, 'system', NOW())
    """
    execute_insert(sql, (task_id, action, old_status, new_status, message))


def dict_to_task_response(row: dict) -> TaskResponse:
    """Convert database row to TaskResponse"""
    return TaskResponse(
        id=row['id'],
        task_name=row['task_name'],
        task_description=row.get('task_description'),
        task_params=row.get('task_params'),
        assigned_to=row['assigned_to'],
        priority=row['priority'],
        status=row['status'],
        progress=row.get('progress', 0),
        created_time=row['created_time'],
        started_time=row.get('started_time'),
        completed_time=row.get('completed_time'),
        result=row.get('result'),
        error_message=row.get('error_message'),
        retry_count=row.get('retry_count', 0),
        created_by=row.get('created_by')
    )


class TaskService:
    """Task service for business logic"""
    
    @staticmethod
    async def list_tasks(
        assigned_to: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[TaskResponse]:
        """List tasks with filters"""
        sql = "SELECT * FROM bot_task WHERE deleted = 0"
        params = []
        
        if assigned_to:
            sql += " AND assigned_to = %s"
            params.append(assigned_to)
        
        if status:
            sql += " AND status = %s"
            params.append(status)
        
        if priority:
            sql += " AND priority = %s"
            params.append(priority)
        
        sql += " ORDER BY created_time DESC"
        
        rows = execute_query(sql, tuple(params) if params else None)
        return [dict_to_task_response(row) for row in rows]
    
    @staticmethod
    async def create_task(task: TaskCreate) -> TaskResponse:
        """Create a new task"""
        sql = """
            INSERT INTO bot_task (
                task_name, task_description, task_params,
                assigned_to, priority, status, created_by
            ) VALUES (%s, %s, %s, %s, %s, 'pending', %s)
        """
        params = (
            task.task_name,
            task.task_description,
            task.task_params,
            task.assigned_to,
            task.priority,
            task.created_by
        )
        
        task_id = execute_insert(sql, params)
        
        # Fetch created task
        row = execute_query("SELECT * FROM bot_task WHERE id = %s", (task_id))[0]
        return dict_to_task_response(row)
    
    @staticmethod
    async def get_task(id: int) -> Optional[TaskResponse]:
        """Get task by ID"""
        rows = execute_query("SELECT * FROM bot_task WHERE id = %s AND deleted = 0", (id,))
        if not rows:
            return None
        return dict_to_task_response(rows[0])
    
    @staticmethod
    async def update_task(id: int, task: TaskUpdate) -> TaskResponse:
        """Update task"""
        # Build dynamic update
        updates = []
        params = []
        
        if task.task_name:
            updates.append("task_name = %s")
            params.append(task.task_name)
        
        if task.task_description:
            updates.append("task_description = %s")
            params.append(task.task_description)
        
        if task.task_params:
            updates.append("task_params = %s")
            params.append(task.task_params)
        
        if task.assigned_to:
            updates.append("assigned_to = %s")
            params.append(task.assigned_to)
        
        if task.priority:
            updates.append("priority = %s")
            params.append(task.priority)
        
        if task.status:
            updates.append("status = %s")
            params.append(task.status)
        
        if task.progress:
            updates.append("progress = %s")
            params.append(task.progress)
        
        if not updates:
            # No updates, just return current task
            return await TaskService.get_task(id)
        
        sql = f"UPDATE bot_task SET {', '.join(updates)} WHERE id = %s"
        params.append(id)
        
        execute_update(sql, tuple(params))
        
        # Fetch updated task
        return await TaskService.get_task(id)
    
    @staticmethod
    async def delete_task(id: int) -> dict:
        """Delete task (soft delete)"""
        execute_update("UPDATE bot_task SET deleted = 1 WHERE id = %s", (id,))
        return {"id": id, "deleted": True}
    
    @staticmethod
    async def get_pending_tasks(assigned_to: str) -> List[TaskResponse]:
        """Get pending tasks for a specific bot (ordered by priority)"""
        sql = """
            SELECT * FROM bot_task 
            WHERE deleted = 0 AND status = 'pending' AND assigned_to = %s
            ORDER BY 
                CASE priority 
                    WHEN 'P0' THEN 0 
                    WHEN 'P1' THEN 1 
                    WHEN 'P2' THEN 2 
                    ELSE 3 
                END,
                created_time ASC
        """
        rows = execute_query(sql, (assigned_to,))
        return [dict_to_task_response(row) for row in rows]
    
    @staticmethod
    async def start_task(id: int) -> TaskResponse:
        """Start task execution"""
        # Get current task to record old status
        task = await TaskService.get_task(id)
        if not task:
            return None
        
        old_status = task.status
        now = datetime.now()
        sql = """
            UPDATE bot_task 
            SET status = 'running', started_time = %s, progress = 0
            WHERE id = %s AND deleted = 0 AND status = 'pending'
        """
        execute_update(sql, (now, id))
        
        # Record log
        add_task_log(id, 'start', old_status, 'running', 'Task started')
        
        return await TaskService.get_task(id)
    
    @staticmethod
    async def complete_task(id: int, result: str) -> TaskResponse:
        """Mark task as completed"""
        # Get current task to record old status
        task = await TaskService.get_task(id)
        if not task:
            return None
        
        old_status = task.status
        now = datetime.now()
        sql = """
            UPDATE bot_task 
            SET status = 'completed', completed_time = %s, progress = 100, result = %s
            WHERE id = %s AND deleted = 0 AND status = 'running'
        """
        execute_update(sql, (now, result, id))
        
        # Record log
        add_task_log(id, 'complete', old_status, 'completed', result)
        
        return await TaskService.get_task(id)
    
    @staticmethod
    async def fail_task(id: int, error_message: str) -> TaskResponse:
        """Mark task as failed"""
        # Get current task to record old status
        task = await TaskService.get_task(id)
        if not task:
            return None
        
        old_status = task.status
        now = datetime.now()
        sql = """
            UPDATE bot_task 
            SET status = 'failed', completed_time = %s, error_message = %s
            WHERE id = %s AND deleted = 0 AND status = 'running'
        """
        execute_update(sql, (now, error_message, id))
        
        # Record log
        add_task_log(id, 'fail', old_status, 'failed', error_message)
        
        return await TaskService.get_task(id)
    
    @staticmethod
    async def retry_task(id: int) -> TaskResponse:
        """Retry failed task"""
        # Check retry count
        task = await TaskService.get_task(id)
        if not task:
            return None
        
        if task.retry_count >= 3:  # max_retry default
            return task  # Cannot retry
        
        # Reset to pending and increment retry count
        old_status = task.status
        sql = """
            UPDATE bot_task 
            SET status = 'pending', started_time = NULL, completed_time = NULL,
                error_message = NULL, retry_count = retry_count + 1
            WHERE id = %s AND deleted = 0 AND status = 'failed'
        """
        execute_update(sql, (id,))
        
        # Record log
        add_task_log(id, 'retry', old_status, 'pending', f'Retry count: {task.retry_count + 1}')
        
        return await TaskService.get_task(id)
    
    @staticmethod
    async def cancel_task(id: int) -> TaskResponse:
        """Cancel task"""
        # Get current task to record old status
        task = await TaskService.get_task(id)
        if not task:
            return None
        
        old_status = task.status
        now = datetime.now()
        sql = """
            UPDATE bot_task 
            SET status = 'cancelled', completed_time = %s
            WHERE id = %s AND deleted = 0 AND status IN ('pending', 'running')
        """
        execute_update(sql, (now, id))
        
        # Record log
        add_task_log(id, 'cancel', old_status, 'cancelled', 'Task cancelled')
        
        return await TaskService.get_task(id)
    
    @staticmethod
    async def get_today_stats() -> dict:
        """Get today's task statistics"""
        sql = """
            SELECT 
                assigned_to,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM bot_task
            WHERE deleted = 0 AND DATE(created_time) = CURDATE()
            GROUP BY assigned_to
        """
        rows = execute_query(sql)
        
        # Convert to dict by assigned_to
        stats = {}
        for row in rows:
            stats[row['assigned_to']] = {
                'total': row['total'],
                'pending': row['pending'],
                'running': row['running'],
                'completed': row['completed'],
                'failed': row['failed']
            }
        
        return stats
    
    @staticmethod
    async def get_task_logs(task_id: int) -> List[dict]:
        """Get task logs"""
        sql = """
            SELECT * FROM bot_task_log 
            WHERE task_id = %s
            ORDER BY created_time DESC
        """
        return execute_query(sql, (task_id,))
