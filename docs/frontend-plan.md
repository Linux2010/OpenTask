# OpenTask 前端管理页面开发评估

> **评估日期：** 2026-05-03
> **评估目标：** 为 OpenTask 服务端开发一个 CRUD 前端管理页面

---

## 1. 现状分析

### 现有 API 端点

| 端点 | 方法 | 功能 | 前端对应操作 |
|------|------|------|-------------|
| `/api/tasks` | GET | 任务列表（可筛选） | 列表页查询 |
| `/api/tasks` | POST | 创建任务 | 新建表单 |
| `/api/tasks/{id}` | GET | 任务详情 | 详情页/编辑页加载 |
| `/api/tasks/{id}` | PUT | 更新任务 | 编辑表单 |
| `/api/tasks/{id}` | DELETE | 删除任务（软删除） | 删除确认 |
| `/api/tasks/pending` | GET | 待执行任务（按 bot） | 任务队列视图 |
| `/api/tasks/{id}/start` | PUT | 开始执行 | 操作按钮 |
| `/api/tasks/{id}/complete` | PUT | 完成任务 | 操作按钮 |
| `/api/tasks/{id}/fail` | PUT | 标记失败 | 操作按钮 |
| `/api/tasks/{id}/retry` | PUT | 重试任务 | 操作按钮 |
| `/api/tasks/{id}/cancel` | PUT | 取消任务 | 操作按钮 |
| `/api/stats/today` | GET | 今日统计 | 仪表盘统计卡片 |
| `/api/logs/{task_id}` | GET | 任务日志 | 日志查看弹窗 |

### 数据模型

```typescript
// Task 类型定义（前端）
interface Task {
  id: number
  task_name: string
  task_description?: string
  task_params?: string  // JSON 字符串
  assigned_to: string   // main/trump/cc/anna/session_agent
  priority: 'P0' | 'P1' | 'P2'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number      // 0-100
  created_time: string
  started_time?: string
  completed_time?: string
  result?: string
  error_message?: string
  retry_count: number
  created_by?: string
}
```

---

## 2. 技术选型评估

### 方案对比

| 方案 | 技术栈 | 优点 | 缺点 | 适用场景 |
|------|--------|------|------|----------|
| **A: 纯静态 HTML** | HTML + Tailwind CDN + Vanilla JS | 最简单、无构建、部署快 | 代码组织差、维护困难 | 快速原型、演示 |
| **B: Vue SPA** | Vue 3 + Vite + Tailwind | 组件化、响应式、生态丰富 | 需构建、学习成本 | 中等规模、长期维护 |
| **C: React SPA** | React + Vite + Tailwind | 组件化、社区大、类型支持好 | 需构建、学习成本 | 中等规模、团队熟悉 React |
| **D: FastAPI 内嵌模板** | Jinja2 + HTMX + Tailwind | 与后端一体、无前端构建 | 不够现代、前后端耦合 | 快速开发、简单页面 |
| **E: Streamlit/FastUI** | Python 低代码框架 | Python 开发、极快 | 定制性差、依赖重 | 内部工具、快速验证 |

### 推荐：方案 B - Vue 3 SPA

**理由：**
1. 组件化开发，代码组织清晰
2. Vite 构建快，开发体验好
3. Tailwind CSS 样式一致，无需写 CSS
4. 学习曲线适中，文档完善
5. 独立部署，不污染后端代码

---

## 3. 功能需求

### 核心页面

| 页面 | 功能 | 优先级 |
|------|------|--------|
| **仪表盘** | 今日统计、任务概览、状态分布 | P1 |
| **任务列表** | 筛选（bot/status/priority）、搜索、分页 | P0 |
| **任务详情** | 查看完整信息、操作日志 | P1 |
| **新建任务** | 表单填写、JSON 参数编辑器 | P0 |
| **编辑任务** | 修改任务信息、状态操作 | P0 |

### 操作功能

| 操作 | 触发方式 | 备注 |
|------|----------|------|
| 创建任务 | 表单提交 | - |
| 编辑任务 | 表单提交 | 仅 pending 状态可编辑 |
| 删除任务 | 确认弹窗 | 软删除 |
| 开始执行 | 按钮 | pending → running |
| 完成任务 | 弹窗输入结果 | running → completed |
| 标记失败 | 弹窗输入错误 | running → failed |
| 重试任务 | 按钮 | failed → pending |
| 取消任务 | 确认弹窗 | pending/running → cancelled |

---

## 4. 页面设计

### 布局结构

```
┌─────────────────────────────────────────────────────┐
│  Header: Logo + 导航 + 用户信息                       │
├─────────────────────────────────────────────────────┤
│  Sidebar: 仪表盘 / 任务列表 / 新建任务 / 设置          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Main Content                                        │
│                                                      │
│  ┌─────────────────────────────────────────────────┐│
│  │  任务列表表格                                    ││
│  │  ┌─────┬──────────┬────────┬────────┬────────┐ ││
│  │  │ ID  │ 任务名称  │ 分配给 │ 状态   │ 操作   │ ││
│  │  ├─────┼──────────┼────────┼────────┼────────┤ ││
│  │  │ 1   │ 给老板打 │ anna   │ pending│ [操作] │ ││
│  │  │ 2   │ 检查上传 │ trump  │ running│ [操作] │ ││
│  │  └─────┴──────────┴────────┴────────┴────────┘ ││
│  │                                                ││
│  │  篩选: [Bot下拉] [状态下拉] [优先级下拉] [搜索] ││
│  └─────────────────────────────────────────────────┘│
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 组件清单

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.vue          # 顶部导航
│   │   │   ├── Sidebar.vue         # 左侧菜单
│   │   │   └── MainLayout.vue      # 布局容器
│   │   ├── Task/
│   │   │   ├── TaskList.vue        # 任务列表表格
│   │   │   ├── TaskForm.vue        # 新建/编辑表单
│   │   │   ├── TaskDetail.vue      # 详情弹窗
│   │   │   ├── TaskActions.vue     # 操作按钮组
│   │   │   ├── TaskFilters.vue     # 篮选控件
│   │   │   └── TaskLogModal.vue    # 日志弹窗
│   │   ├── Dashboard/
│   │   │   ├── StatsCard.vue       # 统计卡片
│   │   │   ├── StatusChart.vue     # 状态分布图
│   │   │   └── PendingQueue.vue    # 待执行队列
│   │   └── Common/
│   │   │   ├── ConfirmDialog.vue   # 确认弹窗
│   │   │   ├── JsonEditor.vue      # JSON 参数编辑
│   │   │   ├── StatusBadge.vue     # 状态标签
│   │   │   └── PriorityBadge.vue   # 优先级标签
│   ├── views/
│   │   ├── DashboardView.vue       # 仪表盘页
│   │   ├── TaskListView.vue        # 任务列表页
│   │   ├── TaskCreateView.vue      # 新建任务页
│   │   ├── TaskEditView.vue        # 编辑任务页
│   ├── api/
│   │   ├── client.ts               # HTTP 客户端（fetch wrapper）
│   │   ├── task.ts                 # Task API 调用
│   │   └── auth.ts                 # API Key 管理
│   ├── stores/
│   │   ├── taskStore.ts            # 任务状态管理（Pinia）
│   │   └── filterStore.ts          # 篮选状态
│   ├── router/
│   │   └── index.ts                # Vue Router 路由
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## 5. 开发工作量估算

### 工时估算（单人）

| 模块 | 工作量 | 说明 |
|------|--------|------|
| 项目初始化 | 2h | Vite + Vue + Tailwind + TypeScript |
| 布局组件 | 4h | Header + Sidebar + MainLayout |
| API 客户端 | 3h | fetch wrapper + API Key + 类型定义 |
| 任务列表 | 6h | 表格 + 篮选 + 分页 + 状态管理 |
| 任务表单 | 4h | 新建/编辑 + JSON 编辑器 |
| 操作功能 | 4h | start/complete/fail/retry/cancel |
| 仪表盘 | 4h | 统计卡片 + 状态图 |
| 弹窗组件 | 3h | 确认弹窗 + 日志弹窗 + 详情弹窗 |
| 路态管理 | 2h | Pinia store + 路由 |
| 样式优化 | 2h | Tailwind 调整 + 响应式 |
| 测试调试 | 4h | 功能测试 + API 联调 |
| **总计** | **~34h** | 约 4-5 个工作日 |

### MVP 简化版（最小可用）

如果时间有限，可先实现 MVP：

| 功能 | 工时 | 说明 |
|------|------|------|
| 任务列表（无筛选） | 4h | 基础表格 |
| 新建任务 | 3h | 简单表单 |
| 编辑/删除 | 3h | 基础操作 |
| 状态操作按钮 | 2h | start/complete |
| **总计** | **~12h** | 约 1.5 个工作日 |

---

## 6. 推荐方案

### 最终推荐：Vue 3 + Vite + Tailwind + TypeScript

**目录结构：**

```
opentask/
├── app/                 # 现有后端
├── frontend/            # 新增前端目录
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docs/
├── CLAUDE.md
└── README.md
```

**开发步骤：**

1. **初始化前端项目**
   ```bash
   cd opentask
   npm create vite@latest frontend -- --template vue-ts
   cd frontend
   npm install tailwindcss @tailwindcss/vite pinia vue-router
   ```

2. **配置 Vite 代理**（开发时连接后端）
   ```ts
   // vite.config.ts
   export default defineConfig({
     server: {
       proxy: {
         '/api': 'http://localhost:8090'
       }
     }
   })
   ```

3. **API Key 存储**
   - localStorage 存储 API Key
   - 每次请求携带 `X-Bot-Key` header
   - 设置页面允许修改 API Key

4. **部署方式**
   - 开发：Vite dev server + proxy
   - 生产：`npm run build` → 静态文件部署到 nginx 或 FastAPI static mount

---

## 7. 替代方案

### 方案 D：FastAPI + Jinja2 + HTMX（最轻量）

如果不想维护独立前端项目，可以在后端直接添加模板页面：

```python
# app/main.py 新增
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/htmx.org"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body>
        <div hx-get="/api/tasks" hx-headers='{"X-Bot-Key": "hope-bot-apikey-2026-0424"}'>
            加载任务列表...
        </div>
    </body>
    </html>
    """
```

**优点：** 无前端构建，与后端一体
**缺点：** 代码耦合，不够现代，定制性差

---

## 8. 决策建议

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| **快速原型/演示** | 方案 A（纯静态）或 方案 D（HTMX） | 最快实现 |
| **长期维护/团队协作** | 方案 B（Vue SPA） | 代码清晰，易维护 |
| **内部工具/无需美观** | 方案 D（HTMX） | 开发快，够用 |
| **Python 团队不熟悉 JS** | 方案 E（Streamlit） | 纯 Python 开发 |

---

## 9. 下一步

如果决定开发前端，建议：

1. 先创建 `frontend/` 目录
2. 初始化 Vite + Vue + TypeScript 项目
3. 先实现 MVP（任务列表 + 新建 + 编辑）
4. 后续迭代添加仪表盘、筛选、日志等功能

**需要资源：**
- 开发者：熟悉 Vue 或 React
- 时间：MVP 1.5 天，完整版 4-5 天

---

**文档作者：** Claude Code
**评估版本：** v1.0