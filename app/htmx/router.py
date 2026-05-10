"""
HTMX + Jinja2 Web Router

Lightweight admin UI using HTMX for dynamic interactions.
"""

import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.task_service import TaskService
from app.services.bot_service import BotService
from app.schemas.task import TaskCreate

router = APIRouter(prefix="/web", tags=["web"])

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Constants
STATUS_OPTIONS = ["pending", "running", "completed", "failed", "cancelled"]
PRIORITY_OPTIONS = ["P0", "P1", "P2"]


# ============== Page Routes (Full HTML) ==============

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    stats = await TaskService.get_today_stats()
    # Flatten stats for template
    flat_stats = {}
    for bot, data in stats.items():
        for key, val in data.items():
            flat_stats[key] = flat_stats.get(key, 0) + val

    # Get recent tasks
    tasks = await TaskService.list_tasks()
    recent_tasks = tasks[:10]  # Show only first 10

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": flat_stats,
            "recent_tasks": recent_tasks,
        }
    )


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_list_page(
    request: Request,
    assigned_to: str = None,
    status: str = None,
    priority: str = None
):
    """Tasks list page"""
    tasks = await TaskService.list_tasks(assigned_to, status, priority)
    bots = await BotService.get_active_bot_names()
    return templates.TemplateResponse(
        "tasks_list.html",
        {
            "request": request,
            "tasks": tasks,
            "bots": bots,
            "statuses": STATUS_OPTIONS,
            "priorities": PRIORITY_OPTIONS,
            "assigned_to": assigned_to,
            "status": status,
            "priority": priority,
        }
    )


@router.get("/tasks/new", response_class=HTMLResponse)
async def task_form_page(request: Request):
    """New task form page"""
    bots = await BotService.get_active_bot_names()
    return templates.TemplateResponse(
        "task_form.html",
        {
            "request": request,
            "bots": bots,
        }
    )


@router.get("/tasks/list", response_class=HTMLResponse)
async def tasks_table_partial(
    request: Request,
    assigned_to: str = None,
    status: str = None,
    priority: str = None
):
    """Tasks table partial for HTMX"""
    tasks = await TaskService.list_tasks(assigned_to, status, priority)
    return templates.TemplateResponse(
        "components/tasks_table.html",
        {
            "request": request,
            "tasks": tasks,
        }
    )


@router.get("/tasks/{id}", response_class=HTMLResponse)
async def task_detail_page(request: Request, id: int):
    """Task detail page"""
    task = await TaskService.get_task(id)
    if not task:
        return HTMLResponse(content="<h1>任务不存在</h1>", status_code=404)

    return templates.TemplateResponse(
        "task_detail.html",
        {
            "request": request,
            "task": task,
        }
    )


@router.post("/api/tasks/create", response_class=HTMLResponse)
async def create_task(request: Request):
    """Create task via HTMX"""
    form_data = await request.form()

    # Collect key-value params
    params = {}
    for i in range(1, 4):
        key = form_data.get(f"param_key_{i}")
        value = form_data.get(f"param_value_{i}")
        if key and value:
            params[key] = value

    task_params = json.dumps(params) if params else None

    task_data = TaskCreate(
        task_name=form_data.get("task_name"),
        task_description=form_data.get("task_description") or None,
        task_params=task_params,
        assigned_to=form_data.get("assigned_to"),
        priority=form_data.get("priority", "P2"),
        created_by=form_data.get("created_by", "admin"),
    )

    task = await TaskService.create_task(task_data)

    return templates.TemplateResponse(
        "components/success_message.html",
        {
            "request": request,
            "message": f"任务 #{task.id} 已创建，分配给 {task.assigned_to}",
            "task_id": task.id,
        }
    )


@router.put("/api/tasks/{id}/start", response_class=HTMLResponse)
async def start_task(request: Request, id: int):
    """Start task via HTMX"""
    task = await TaskService.start_task(id)
    if not task:
        return HTMLResponse(content="<span class='text-red-500'>操作失败</span>")

    # Return updated row
    return templates.TemplateResponse(
        "components/tasks_table.html",
        {
            "request": request,
            "tasks": [task],
        }
    )


@router.get("/tasks/{id}/complete-form", response_class=HTMLResponse)
async def complete_form_partial(request: Request, id: int):
    """Complete task form for modal"""
    task = await TaskService.get_task(id)
    return templates.TemplateResponse(
        "components/complete_form.html",
        {
            "request": request,
            "task": task,
        }
    )


@router.post("/api/tasks/{id}/complete", response_class=HTMLResponse)
async def complete_task(request: Request, id: int):
    """Complete task via HTMX"""
    form_data = await request.form()
    result = form_data.get("result", "")

    task = await TaskService.complete_task(id, result)
    if not task:
        return HTMLResponse(content="<div class='p-6 text-red-500'>操作失败</div>")

    return templates.TemplateResponse(
        "components/success_message.html",
        {
            "request": request,
            "message": f"任务 #{id} 已完成",
            "task_id": id,
        }
    )


@router.get("/tasks/{id}/fail-form", response_class=HTMLResponse)
async def fail_form_partial(request: Request, id: int):
    """Fail task form for modal"""
    task = await TaskService.get_task(id)
    return templates.TemplateResponse(
        "components/fail_form.html",
        {
            "request": request,
            "task": task,
        }
    )


@router.post("/api/tasks/{id}/fail", response_class=HTMLResponse)
async def fail_task(request: Request, id: int):
    """Fail task via HTMX"""
    form_data = await request.form()
    error_message = form_data.get("error_message", "")

    task = await TaskService.fail_task(id, error_message)
    if not task:
        return HTMLResponse(content="<div class='p-6 text-red-500'>操作失败</div>")

    return templates.TemplateResponse(
        "components/success_message.html",
        {
            "request": request,
            "message": f"任务 #{id} 已标记失败",
            "task_id": id,
        }
    )


@router.put("/api/tasks/{id}/retry", response_class=HTMLResponse)
async def retry_task(request: Request, id: int):
    """Retry task via HTMX"""
    task = await TaskService.retry_task(id)
    if not task:
        return HTMLResponse(content="<span class='text-red-500'>操作失败：无法重试</span>")

    return templates.TemplateResponse(
        "components/success_message.html",
        {
            "request": request,
            "message": f"任务 #{id} 已重新排队",
            "task_id": id,
        }
    )


@router.put("/api/tasks/{id}/cancel", response_class=HTMLResponse)
async def cancel_task(request: Request, id: int):
    """Cancel task via HTMX"""
    task = await TaskService.cancel_task(id)
    if not task:
        return HTMLResponse(content="<span class='text-red-500'>操作失败</span>")

    return templates.TemplateResponse(
        "components/success_message.html",
        {
            "request": request,
            "message": f"任务 #{id} 已取消",
            "task_id": id,
        }
    )


@router.get("/api/tasks/{id}/logs", response_class=HTMLResponse)
async def task_logs_partial(request: Request, id: int):
    """Task logs partial for HTMX"""
    logs = await TaskService.get_task_logs(id)
    return templates.TemplateResponse(
        "components/logs_table.html",
        {
            "request": request,
            "logs": logs,
        }
    )


@router.get("/api/stats/refresh", response_class=HTMLResponse)
async def refresh_stats(request: Request):
    """Refresh stats for HTMX"""
    stats = await TaskService.get_today_stats()
    flat_stats = {}
    for bot, data in stats.items():
        for key, val in data.items():
            flat_stats[key] = flat_stats.get(key, 0) + val

    tasks = await TaskService.list_tasks()
    recent_tasks = tasks[:10]

    return templates.TemplateResponse(
        "components/tasks_table.html",
        {
            "request": request,
            "tasks": recent_tasks,
        }
    )


# ============== Bot Management Routes ==============

@router.get("/bots", response_class=HTMLResponse)
async def bots_list_page(request: Request):
    """Bot management page"""
    bots = await BotService.list_bots()
    return templates.TemplateResponse(
        "bots_list.html",
        {
            "request": request,
            "bots": bots,
        }
    )


@router.post("/api/bots/create", response_class=HTMLResponse)
async def create_bot(request: Request):
    """Create new bot via HTMX"""
    form_data = await request.form()
    bot_name = form_data.get("bot_name")
    display_name = form_data.get("display_name")
    description = form_data.get("description")

    try:
        bot = await BotService.create_bot(bot_name, display_name, description)
        # Return success and close modal
        return HTMLResponse(content=f"""
            <div class="p-6">
                <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
                    Bot <strong>{bot_name}</strong> 已添加成功
                </div>
                <script>
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 500);
                </script>
            </div>
        """)
    except Exception as e:
        return HTMLResponse(content=f"""
            <div class="p-6">
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
                    添加失败：{str(e)}
                </div>
            </div>
        """)


@router.put("/api/bots/{bot_name}/toggle", response_class=HTMLResponse)
async def toggle_bot_status(request: Request, bot_name: str):
    """Toggle bot active status"""
    bot = await BotService.toggle_bot_status(bot_name)
    if not bot:
        return HTMLResponse(content="<span class='text-red-500'>操作失败</span>")

    return templates.TemplateResponse(
        "components/bot_row.html",
        {
            "request": request,
            "bot": bot[0],
        }
    )


@router.delete("/api/bots/{bot_name}", response_class=HTMLResponse)
async def delete_bot(request: Request, bot_name: str):
    """Delete a bot"""
    success = await BotService.delete_bot(bot_name)
    if success:
        return HTMLResponse(content="")  # Empty response removes the row
    return HTMLResponse(content="<span class='text-red-500'>删除失败</span>")