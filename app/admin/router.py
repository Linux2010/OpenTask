"""
OpenTask Admin UI Router

FastUI routes for task management frontend.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastui import FastUI
from fastui.components import (
    PageTitle, Heading, Text, Div, Table,
    Form, FormField, Button, Link
)
from fastui.components.forms import FormFieldInput, FormFieldSelect, FormFieldTextarea
from fastui.events import GoToEvent
from typing import List, Optional
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate

router = APIRouter(prefix="/admin", tags=["admin"])

# Bot 身份选项
BOT_OPTIONS = ["main", "trump", "cc", "anna", "session_agent"]
STATUS_OPTIONS = ["pending", "running", "completed", "failed", "cancelled"]
PRIORITY_OPTIONS = ["P0", "P1", "P2"]


def make_select_options(values: List[str]) -> List[dict]:
    """Create select options for FormFieldSelect"""
    return [{"value": v, "label": v} for v in values]


def spacer(height: int = 20) -> Div:
    """Create a spacer div"""
    return Div(components=[], class_name=f"spacer-h-{height}")


def stats_card(title: str, value: int) -> Div:
    """Create stats card"""
    return Div(
        components=[Text(text=f"{title}: {value}")],
        class_name="stats-card"
    )


def task_info_row(label: str, value: str) -> Div:
    """Create a task info row"""
    return Div(
        components=[Text(text=f"{label}: {value}")],
        class_name="info-row"
    )


@router.get("/", response_model=FastUI)
async def dashboard():
    """Dashboard page - today's stats"""
    stats = await TaskService.get_today_stats()

    return [
        PageTitle(text="OpenTask 仪表盘"),
        Heading(text="OpenTask 任务管理"),
        spacer(20),
        Div(
            components=[
                Heading(text="今日统计", level=2),
                Div(
                    components=[
                        stats_card("待执行", stats.get("pending", 0)),
                        stats_card("执行中", stats.get("running", 0)),
                        stats_card("已完成", stats.get("completed", 0)),
                        stats_card("失败", stats.get("failed", 0)),
                    ],
                    class_name="stats-grid"
                ),
            ],
            class_name="dashboard-section"
        ),
        spacer(30),
        Div(
            components=[
                Heading(text="快速操作", level=2),
                Div(
                    components=[
                        Link(components=[Text(text="查看所有任务")], on_click=GoToEvent(url="/admin/tasks")),
                        Link(components=[Text(text="快速派任务")], on_click=GoToEvent(url="/admin/tasks/new")),
                    ],
                    class_name="quick-actions"
                ),
            ],
            class_name="dashboard-section"
        ),
    ]


@router.get("/tasks", response_model=FastUI)
async def task_list(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None
):
    """Task list page with filters"""
    tasks = await TaskService.list_tasks(assigned_to, status, priority)

    # Build filter options with empty option
    status_opts = [{"value": "", "label": "全部状态"}] + make_select_options(STATUS_OPTIONS)
    bot_opts = [{"value": "", "label": "全部 Bot"}] + make_select_options(BOT_OPTIONS)
    priority_opts = [{"value": "", "label": "全部优先级"}] + make_select_options(PRIORITY_OPTIONS)

    # Prepare table data
    table_data = []
    for t in tasks:
        table_data.append({
            "ID": t["id"],
            "任务名称": t["task_name"],
            "分配对象": t["assigned_to"],
            "状态": t["status"],
            "优先级": t["priority"],
            "进度": f"{t.get('progress', 0)}%",
        })

    return [
        PageTitle(text=title)"任务列表"),
        Heading(text="任务列表"),
        spacer(20),
        Div(
            components=[
                Heading(text="筛选", level=3),
                Form(
                    submit_url="/admin/tasks",
                    method="GET",
                    form_fields=[
                        FormField(
                            FormFieldSelect(
                                name="status",
                                title="状态",
                                options=status_opts,
                                initial=status or ""
                            )
                        ),
                        FormField(
                            FormFieldSelect(
                                name="assigned_to",
                                title="分配对象",
                                options=bot_opts,
                                initial=assigned_to or ""
                            )
                        ),
                        FormField(
                            FormFieldSelect(
                                name="priority",
                                title="优先级",
                                options=priority_opts,
                                initial=priority or ""
                            )
                        ),
                    ],
                ),
            ],
            class_name="filter-section"
        ),
        spacer(20),
        Div(
            components=[
                Link(components=[Text(text="快速派任务")], on_click=GoToEvent(url= "/admin/tasks/new"}),
                Text(text=f"共 {len(tasks)} 个任务"),
            ],
            class_name="task-header"
        ),
        spacer(10),
        Table(data=table_data) if table_data else Text(text="暂无任务"),
        spacer(20),
        Heading(text="任务详情链接", level=3),
        Div(
            components=[
                Div(
                    components=[
                        Link(components=[Text(text=f"#{t['id']} - {t['task_name']} ({t['status']})")], on_click=GoToEvent(url= f"/admin/tasks/{t['id']}"}),
                    ],
                    class_name="task-link-row"
                )
                for t in tasks
            ],
            class_name="task-links"
        ) if tasks else None,
    ]


@router.get("/tasks/new", response_model=FastUI)
async def task_create_form():
    """Create task form page"""
    bot_opts = make_select_options(BOT_OPTIONS)
    priority_opts = make_select_options(PRIORITY_OPTIONS)

    return [
        PageTitle(text=title)"创建任务"),
        Heading(text="快速派任务"),
        spacer(20),
        Form(
            submit_url="/admin/tasks/create",
            method="POST",
            form_fields=[
                FormField(
                    FormFieldInput(
                        name="task_name",
                        title="任务名称",
                        required=True,
                        placeholder="输入任务名称"
                    )
                ),
                FormField(
                    FormFieldTextarea(
                        name="task_description",
                        title="任务描述",
                        placeholder="输入任务描述（可选）"
                    )
                ),
                FormField(
                    FormFieldTextarea(
                        name="task_params",
                        title="任务参数 (JSON)",
                        placeholder='{"key": "value"}'
                    )
                ),
                FormField(
                    FormFieldSelect(
                        name="assigned_to",
                        title="分配对象",
                        options=bot_opts,
                        required=True,
                        initial="main"
                    )
                ),
                FormField(
                    FormFieldSelect(
                        name="priority",
                        title="优先级",
                        options=priority_opts,
                        initial="P2"
                    )
                ),
                FormField(
                    FormFieldInput(
                        name="created_by",
                        title="创建者",
                        initial="admin"
                    )
                ),
            ],
        ),
        spacer(20),
        Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"}),
    ]


@router.post("/tasks/create", response_model=FastUI)
async def task_create_submit(request: Request):
    """Handle task creation"""
    form_data = await request.form()

    task_data = TaskCreate(
        task_name=form_data.get("task_name"),
        task_description=form_data.get("task_description") or None,
        task_params=form_data.get("task_params") or None,
        assigned_to=form_data.get("assigned_to"),
        priority=form_data.get("priority", "P2"),
        created_by=form_data.get("created_by", "admin"),
    )

    task = await TaskService.create_task(task_data)

    return [
        PageTitle(text=title)"任务创建成功"),
        Heading(text="任务创建成功"),
        spacer(20),
        Text(text=f"任务 ID: {task['id']} 已创建"),
        spacer(20),
        Div(
            components=[
                Link(components=[Text(text="查看任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{task['id']}"}),
                Link(components=[Text(text="继续创建任务")], on_click=GoToEvent(url= "/admin/tasks/new"}),
                Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"}),
            ]
        ),
    ]


@router.get("/tasks/{id}", response_model=FastUI)
async def task_detail(id: int):
    """Task detail page"""
    task = await TaskService.get_task(id)
    if not task:
        return [
            PageTitle(text=title)"任务不存在"),
            Heading(text="任务不存在"),
            Text(text=f"任务 ID {id} 未找到"),
            spacer(20),
            Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"}),
        ]

    # Determine available actions based on status
    status = task["status"]
    action_links = []

    if status == "pending":
        action_links.append(Link(components=[Text(text="开始执行")], on_click=GoToEvent(url= f"/admin/tasks/{id}/start"}))
    if status == "running":
        action_links.extend([
            Link(components=[Text(text="标记完成")], on_click=GoToEvent(url= f"/admin/tasks/{id}/complete"}),
            Link(components=[Text(text="标记失败")], on_click=GoToEvent(url= f"/admin/tasks/{id}/fail"}),
        ])
    if status == "failed":
        action_links.append(Link(components=[Text(text="重试任务")], on_click=GoToEvent(url= f"/admin/tasks/{id}/retry"}))
    if status in ["pending", "running"]:
        action_links.append(Link(components=[Text(text="取消任务")], on_click=GoToEvent(url= f"/admin/tasks/{id}/cancel"}))

    return [
        PageTitle(text=title)f"任务详情 - {task['task_name']}"),
        Heading(text=f"任务 #{id}"),
        spacer(20),
        Div(
            components=[
                Heading(text="基本信息", level=2),
                task_info_row("任务名称", task["task_name"]),
                task_info_row("任务描述", task.get("task_description") or "无"),
                task_info_row("任务参数", task.get("task_params") or "无"),
                task_info_row("分配对象", task["assigned_to"]),
                task_info_row("优先级", task["priority"]),
                task_info_row("状态", task["status"]),
                task_info_row("进度", f"{task.get('progress', 0)}%"),
            ],
            class_name="info-section"
        ),
        spacer(20),
        Div(
            components=[
                Heading(text="时间信息", level=2),
                task_info_row("创建时间", str(task.get("created_time", ""))),
                task_info_row("开始时间", str(task.get("started_time") or "未开始")),
                task_info_row("完成时间", str(task.get("completed_time") or "未完成")),
            ],
            class_name="info-section"
        ),
        spacer(20),
        Div(
            components=[
                Heading(text="执行结果", level=2),
                task_info_row("执行结果", task.get("result") or "无"),
                task_info_row("错误信息", task.get("error_message") or "无"),
                task_info_row("重试次数", str(task.get("retry_count", 0))),
                task_info_row("创建者", task.get("created_by") or "未知"),
            ],
            class_name="info-section"
        ),
        spacer(30),
        Heading(text="操作", level=2),
        Div(
            components=action_links + [Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"})],
            class_name="task-actions"
        ) if action_links else Div(
            components=[Text(text="无可用操作"), Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"})],
        ),
    ]


@router.get("/tasks/{id}/start", response_model=FastUI)
async def task_start(id: int):
    """Start task"""
    task = await TaskService.start_task(id)
    if not task:
        return [
            PageTitle(text=title)"操作失败"),
            Heading(text="无法开始任务"),
            Text(text=f"任务 ID {id} 无法开始"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"任务已开始"),
        Heading(text="任务已开始执行"),
        Text(text=f"任务 #{id} 状态已更新为 running"),
        spacer(20),
        Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
    ]


@router.get("/tasks/{id}/complete", response_model=FastUI)
async def task_complete_form(id: int):
    """Complete task form"""
    task = await TaskService.get_task(id)
    if not task or task["status"] != "running":
        return [
            PageTitle(text=title)"操作失败"),
            Heading(text="无法完成任务"),
            Text(text=f"任务 ID {id} 无法完成"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"标记任务完成"),
        Heading(text=f"标记任务 #{id} 完成"),
        Form(
            submit_url=f"/admin/tasks/{id}/complete/submit",
            method="POST",
            form_fields=[
                FormField(
                    FormFieldTextarea(
                        name="result",
                        title="执行结果",
                        required=True,
                        placeholder="输入执行结果"
                    )
                ),
            ],
        ),
    ]


@router.post("/tasks/{id}/complete/submit", response_model=FastUI)
async def task_complete_submit(id: int, request: Request):
    """Submit task completion"""
    form_data = await request.form()
    result = form_data.get("result", "")

    task = await TaskService.complete_task(id, result)
    if not task:
        return [
            Heading(text="操作失败"),
            Text(text="无法完成任务"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"任务已完成"),
        Heading(text="任务已完成"),
        Text(text=f"任务 #{id} 状态已更新为 completed"),
        spacer(20),
        Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"}),
    ]


@router.get("/tasks/{id}/fail", response_model=FastUI)
async def task_fail_form(id: int):
    """Fail task form"""
    task = await TaskService.get_task(id)
    if not task or task["status"] != "running":
        return [
            PageTitle(text=title)"操作失败"),
            Heading(text="无法标记失败"),
            Text(text=f"任务 ID {id} 无法标记为失败"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"标记任务失败"),
        Heading(text=f"标记任务 #{id} 失败"),
        Form(
            submit_url=f"/admin/tasks/{id}/fail/submit",
            method="POST",
            form_fields=[
                FormField(
                    FormFieldTextarea(
                        name="error_message",
                        title="错误信息",
                        required=True,
                        placeholder="输入错误信息"
                    )
                ),
            ],
        ),
    ]


@router.post("/tasks/{id}/fail/submit", response_model=FastUI)
async def task_fail_submit(id: int, request: Request):
    """Submit task failure"""
    form_data = await request.form()
    error_message = form_data.get("error_message", "")

    task = await TaskService.fail_task(id, error_message)
    if not task:
        return [
            Heading(text="操作失败"),
            Text(text="无法标记任务失败"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"任务已标记失败"),
        Heading(text="任务已标记失败"),
        Text(text=f"任务 #{id} 状态已更新为 failed"),
        spacer(20),
        Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"}),
    ]


@router.get("/tasks/{id}/retry", response_model=FastUI)
async def task_retry(id: int):
    """Retry task"""
    task = await TaskService.retry_task(id)
    if not task:
        return [
            PageTitle(text=title)"操作失败"),
            Heading(text="无法重试任务"),
            Text(text=f"任务 ID {id} 无法重试"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"任务已重试"),
        Heading(text="任务已重新排队"),
        Text(text=f"任务 #{id} 状态已更新为 pending"),
        spacer(20),
        Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
    ]


@router.get("/tasks/{id}/cancel", response_model=FastUI)
async def task_cancel(id: int):
    """Cancel task"""
    task = await TaskService.cancel_task(id)
    if not task:
        return [
            PageTitle(text=title)"操作失败"),
            Heading(text="无法取消任务"),
            Text(text=f"任务 ID {id} 无法取消"),
            Link(components=[Text(text="返回任务详情")], on_click=GoToEvent(url= f"/admin/tasks/{id}"}),
        ]

    return [
        PageTitle(text=title)"任务已取消"),
        Heading(text="任务已取消"),
        Text(text=f"任务 #{id} 状态已更新为 cancelled"),
        spacer(20),
        Link(components=[Text(text="返回任务列表")], on_click=GoToEvent(url= "/admin/tasks"}),
    ]