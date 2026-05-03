# OpenTask FastUI 技术方案

> **创建日期：** 2026-05-03
> **目标：** 使用 FastUI 为 OpenTask 开发管理前端

---

## 1. 页面路由设计

| 路径 | 页面 | 功能 |
|------|------|------|
| `/admin/` | 仪表盘 | 今日统计、任务概览 |
| `/admin/tasks` | 任务列表 | 显示所有任务，支持筛选 |
| `/admin/tasks/{id}` | 任务详情 | 查看详情、操作按钮 |
| `/admin/tasks/new` | 创建任务 | 快速派任务表单 |

---

## 2. FastUI 组件选型

| 功能 | FastUI 组件 | 说明 |
|------|-------------|------|
| 页面标题 | `PageTitle` | 设置浏览器标题 |
| 标题文本 | `Heading` | H1/H2 标题 |
| 统计卡片 | `Div` + `Text` | 自定义布局 |
| 数据表格 | `Table` | 显示任务列表 |
| 篮选表单 | `Form` + `Select` | 下拉筛选 |
| 任务表单 | `Form` + `TextInput`/`TextArea` | 创建/编辑任务 |
| 操作按钮 | `Button` | 开始、完成、失败等 |
| 详情展示 | `Details` | 任务详情折叠面板 |
| 弹窗确认 | `Modal` | 删除/取消确认 |

---

## 3. 键值对表单输入方案

`task_params` 字段需要支持动态键值对输入，方案：

**方案 A：TextArea + JSON 格式**
- 使用 `TextArea` 组件
- 用户输入 JSON 字符串，如 `{"key": "value"}`
- 简单实现，适合熟悉 JSON 的用户

**方案 B：动态键值对组件**
- 使用自定义 `Div` 嵌套多个 `TextInput`
- 每行一个键值对，支持添加/删除
- 需要前端 JavaScript 支持（FastUI 目前限制）

**选择方案 A**，后续可迭代优化。

---

## 4. 与后端 API 对接方式

FastUI 页面通过 HTTP 请求调用现有 API：

```python
# 方式 1：直接调用 Service 层（推荐）
from app.services.task_service import TaskService
data = await TaskService.list_tasks()

# 方式 2：内部 HTTP 请求（需要处理 API Key）
import httpx
resp = await httpx.get("http://localhost:8090/api/tasks", headers={"X-Bot-Key": "..."})
```

**采用方式 1**，直接调用 Service 层，绕过 API Key 验证（管理端内置）。

---

## 5. 组件结构

```
app/admin/
├── __init__.py
├── router.py          # FastUI 路由定义
├── components.py      # 共享组件函数
└── forms.py           # 表单定义（可选）
```

---

## 6. 关键代码示例

### 仪表盘页面
```python
@router.get("/", response_model=FastUI)
async def dashboard():
    stats = await TaskService.get_today_stats()
    return [
        PageTitle(title="OpenTask 仪表盘"),
        Heading(text="今日统计"),
        Div(components=[
            Text(text=f"待执行: {stats['pending']}"),
            Text(text=f"执行中: {stats['running']}"),
            Text(text=f"已完成: {stats['completed']}"),
            Text(text=f"失败: {stats['failed']}"),
        ]),
    ]
```

### 任务列表页面
```python
@router.get("/tasks", response_model=FastUI)
async def task_list(status: str = None, assigned_to: str = None):
    tasks = await TaskService.list_tasks(assigned_to, status)
    return [
        PageTitle(title="任务列表"),
        Heading(text="所有任务"),
        Table(data=[task_to_row(t) for t in tasks]),
    ]
```

---

## 7. 依赖版本

```
fastui>=0.7.0
```

---

## 8. 开发步骤

1. 添加 fastui 到 requirements.txt
2. 创建 `app/admin/` 目录结构
3. 实现仪表盘页面
4. 实现任务列表页面（带筛选）
5. 实现创建任务表单
6. 实现任务详情页面（带操作按钮）
7. 在 main.py 注册路由
8. 测试运行

---

**文档作者：** Claude Code