# Bot TodoList 极简版设计文档

> **设计原则：保留核心功能，删除过度设计**
> 
> 创建时间：2026-04-24 19:36
> 更新时间：2026-04-24 19:36
> 作者：Hope

---

## 1. 设计背景

### 1.1 为什么选择极简版？

| 原因 | 说明 |
|------|------|
| **快速上线** | 2 张表 vs 7 张表，开发时间从 6-7 天缩短到 3-4 天 |
| **易于维护** | 23 个字段 vs 100+ 个字段，维护成本低 |
| **聚焦核心** | 任务分发 + 进度跟踪 + 审计日志，满足核心需求 |
| **避免过度设计** | 删除不必要的字段和表，避免后期维护负担 |

### 1.2 技术栈选择

| 组件 | 技术 | 说明 |
|------|------|------|
| **数据库** | MySQL 8.0 | hope05:53306，与 Hope 系统统一管理 |
| **Web 框架** | FastAPI | 异步、高性能、自动文档生成 |
| **数据库驱动** | pymysql | MySQL 连接 |
| **认证** | API Key | X-Bot-Key 请求头 |
| **部署** | Docker + systemd | 容器部署或 systemd 服务 |

---

## 2. 数据库设计（极简版）

### 2.1 表结构（2 张表）

| 表名 | 字段数 | 说明 |
|------|--------|------|
| **bot_task** | 16 | 核心任务表 |
| **bot_task_log** | 7 | 审计日志表 |

---

### 2.2 bot_task 表结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **id** | BIGINT(20) | ✅ | 任务 ID（自增） |
| **task_name** | VARCHAR(100) | ✅ | 任务名称 |
| **task_description** | TEXT | ❌ | 任务描述 |
| **task_params** | TEXT | ❌ | 任务参数（JSON 格式） |
| **assigned_to** | VARCHAR(50) | ✅ | 分配对象（trump/cc/anna/main/session_agent） |
| **priority** | VARCHAR(10) | ✅ | 优先级（P0 紧急 / P1 重要 / P2 一般） |
| **status** | VARCHAR(20) | ✅ | 状态（pending/running/completed/failed/cancelled） |
| **progress** | INT(11) | ❌ | 执行进度（0-100） |
| **created_time** | DATETIME | ✅ | 创建时间 |
| **started_time** | DATETIME | ❌ | 开始时间 |
| **completed_time** | DATETIME | ❌ | 完成时间 |
| **result** | TEXT | ❌ | 执行结果 |
| **error_message** | TEXT | ❌ | 错误信息 |
| **retry_count** | INT(11) | ❌ | 已重试次数（默认 0） |
| **max_retry** | INT(11) | ❌ | 最大重试次数（默认 3） |
| **created_by** | VARCHAR(50) | ✅ | 创建者（hope/manual） |
| **deleted** | TINYINT(1) | ❌ | 删除标记（默认 0） |
| **update_time** | DATETIME | ❌ | 更新时间 |

**索引：**
- PRIMARY KEY (`id`)
- INDEX `idx_assigned_to` (`assigned_to`)
- INDEX `idx_status` (`status`)
- INDEX `idx_priority` (`priority`)
- INDEX `idx_assigned_status` (`assigned_to`, `status`)
- INDEX `idx_created_time` (`created_time`)

---

### 2.3 bot_task_log 表结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **id** | BIGINT(20) | ✅ | 日志 ID（自增） |
| **task_id** | BIGINT(20) | ✅ | 任务 ID |
| **action** | VARCHAR(50) | ✅ | 动作（created/started/completed/failed/retried/cancelled） |
| **message** | TEXT | ❌ | 日志信息 |
| **old_status** | VARCHAR(20) | ❌ | 原状态 |
| **new_status** | VARCHAR(20) | ❌ | 新状态 |
| **operator** | VARCHAR(50) | ❌ | 操作者 |
| **created_time** | DATETIME | ✅ | 创建时间 |

**索引：**
- PRIMARY KEY (`id`)
- INDEX `idx_task_id` (`task_id`)
- INDEX `idx_action` (`action`)
- INDEX `idx_created_time` (`created_time`)

---

### 2.4 触发器（自动记录日志）

```sql
-- 任务创建时记录日志
CREATE TRIGGER tr_bot_task_created 
AFTER INSERT ON bot_task
FOR EACH ROW
BEGIN
  INSERT INTO bot_task_log (task_id, action, message, new_status, operator, created_time)
  VALUES (NEW.id, 'created', CONCAT('创建任务：', NEW.task_name), NEW.status, NEW.created_by, NOW());
END;

-- 任务状态变更时记录日志
CREATE TRIGGER tr_bot_task_status_change 
AFTER UPDATE ON bot_task
FOR EACH ROW
BEGIN
  IF OLD.status != NEW.status THEN
    INSERT INTO bot_task_log (task_id, action, message, old_status, new_status, operator, created_time)
    VALUES (NEW.id, 
      CASE NEW.status WHEN 'running' THEN 'started' WHEN 'completed' THEN 'completed' ELSE NEW.status END,
      CONCAT('状态变更：', OLD.status, ' → ', NEW.status),
      OLD.status, NEW.status, NEW.assigned_to, NOW());
  END IF;
END;
```

---

### 2.5 视图（常用查询）

| 视图名 | 说明 |
|------|------|
| **v_bot_pending** | 待执行任务视图（按优先级排序） |
| **v_bot_today_stats** | 今日任务统计视图 |

---

### 2.6 状态流转

```
pending → running → completed
                   ↘ failed → (retry) → running
                   ↘ cancelled
```

| 状态 | 说明 |
|------|------|
| **pending** | 待执行（等待 bot 认领） |
| **running** | 执行中（bot 正在处理） |
| **completed** | 已完成（执行成功） |
| **failed** | 失败（执行失败，可重试） |
| **cancelled** | 已取消（人工取消） |

---

### 2.7 优先级说明

| 优先级 | 说明 | 使用场景 |
|--------|------|----------|
| **P0** | 紧急 | 系统故障、紧急通知 |
| **P1** | 重要 | 重要任务、每日例行 |
| **P2** | 一般 | 测试任务、非紧急操作 |

---

### 2.8 task_params JSON 格式示例

```json
{
  "telegram_id": "5520269161",
  "message": "老板早上好！",
  "steps": [
    "检查 Telegram 连接",
    "构建祝福语",
    "发送消息",
    "确认发送成功"
  ],
  "input": {
    "video_path": "/tmp/test.mp4"
  },
  "output": {
    "message_id": "12345"
  }
}
```

**说明：**
- task_params 是一个 JSON 字符串，包含所有任务参数
- 可以包含 steps（执行步骤）、input（输入数据）、output（输出数据）
- 灵活扩展，不需要额外字段

---

## 3. Python 服务设计

### 3.1 项目结构

```
~/hope-bot-service/
├── app/
│   ├── __init__.py              # FastAPI 应用初始化
│   ├── main.py                  # 入口文件
│   ├── config.py                # 配置文件
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py              # Task 模型（极简版）
│   │   └── task_log.py          # TaskLog 模型
│   ├── routers/
│   │   ├── __init__.py
│   │   └── task.py              # Task API 路由
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py      # Task 业务逻辑
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db.py                # 数据库连接
│   │   └── auth.py              # API Key 认证
│   └── schemas/
│       ├── __init__.py
│       ├── task.py              # Task Pydantic 模型
│       └── response.py          # 响应模型
├── tests/
│   ├── test_task_api.py         # API 测试
│   └── test_task_service.py     # 服务测试
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 配置
├── docker-compose.yml           # Docker Compose 配置
├── .env                         # 环境变量
└── README.md                    # 项目文档
```

---

### 3.2 API 接口设计

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tasks` | GET | 获取任务列表（按优先级排序） |
| `/api/tasks` | POST | 创建任务 |
| `/api/tasks/{id}` | GET | 获取任务详情 |
| `/api/tasks/{id}` | PUT | 更新任务状态 |
| `/api/tasks/{id}` | DELETE | 删除任务（软删除） |
| `/api/tasks/pending` | GET | 获取待执行任务（按 bot 分组） |
| `/api/tasks/{id}/start` | PUT | 开始执行任务 |
| `/api/tasks/{id}/complete` | PUT | 完成任务 |
| `/api/tasks/{id}/fail` | PUT | 标记任务失败 |
| `/api/tasks/{id}/retry` | PUT | 重试任务 |
| `/api/tasks/{id}/cancel` | PUT | 取消任务 |
| `/api/stats/today` | GET | 今日任务统计 |
| `/api/logs/{task_id}` | GET | 获取任务日志 |

---

### 3.3 API Key 认证

**请求头：**
```
X-Bot-Key: hope-bot-apikey-2026-0424
```

**认证流程：**
1. 请求到达 FastAPI
2. 中间件检查 X-Bot-Key 请求头
3. 验证 API Key 是否正确
4. 验证失败返回 401 Unauthorized

---

### 3.4 配置文件（config.py）

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DB_HOST: str = "hope05"
    DB_PORT: int = 53306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Tianfs@2020!!"
    DB_NAME: str = "hope_engine"
    
    # API Key
    API_KEY: str = "hope-bot-apikey-2026-0424"
    
    # 服务配置
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

### 3.5 Task 模型（models/task.py）

```python
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, TinyInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class BotTask(Base):
    __tablename__ = "bot_task"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False)
    task_description = Column(Text)
    task_params = Column(Text)
    assigned_to = Column(String(50), nullable=False)
    priority = Column(String(10), nullable=False, default="P2")
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)
    created_time = Column(DateTime, nullable=False, server_default=func.now())
    started_time = Column(DateTime)
    completed_time = Column(DateTime)
    result = Column(Text)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retry = Column(Integer, default=3)
    created_by = Column(String(50), nullable=False)
    deleted = Column(TinyInteger, default=0)
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

---

### 3.6 API 路由示例（routers/task.py）

```python
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """获取任务列表"""
    return await TaskService.list_tasks(assigned_to, status, priority)

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    api_key: str = Depends(verify_api_key)
):
    """创建任务"""
    return await TaskService.create_task(task)

@router.get("/pending", response_model=List[TaskResponse])
async def get_pending_tasks(
    assigned_to: str,
    api_key: str = Depends(verify_api_key)
):
    """获取指定 bot 的待执行任务"""
    return await TaskService.get_pending_tasks(assigned_to)

@router.put("/{id}/start", response_model=TaskResponse)
async def start_task(
    id: int,
    api_key: str = Depends(verify_api_key)
):
    """开始执行任务"""
    return await TaskService.start_task(id)

@router.put("/{id}/complete", response_model=TaskResponse)
async def complete_task(
    id: int,
    result: str,
    api_key: str = Depends(verify_api_key)
):
    """完成任务"""
    return await TaskService.complete_task(id, result)

@router.put("/{id}/fail", response_model=TaskResponse)
async def fail_task(
    id: int,
    error_message: str,
    api_key: str = Depends(verify_api_key)
):
    """标记任务失败"""
    return await TaskService.fail_task(id, error_message)
```

---

## 4. HEARTBEAT 集成

### 4.1 HEARTBEAT.md 模板

```markdown
# HEARTBEAT.md

## Bot 任务检查

在 heartbeat 时，调用 Bot TodoList API 获取待执行任务：

### API 地址
http://hope05:8090/api/tasks/pending?assigned_to=anna

### 请求头
X-Bot-Key: hope-bot-apikey-2026-0424

### 心跳流程
1. 调用 API 获取待执行任务
2. 如果有 P0 任务，立即执行并通知用户
3. 如果有 P1 任务，按顺序执行
4. 如果有 P2 任务，有时间时执行
5. 执行完成后，调用 API 更新状态

### 命令示例
```bash
# 获取待执行任务
curl -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=anna"

# 开始执行任务
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/start"

# 完成任务
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/complete" \
  -d '{"result":"执行成功"}'

# 标记失败
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/fail" \
  -d '{"error_message":"连接失败"}'
```
```

---

## 5. 开发计划

### 5.1 开发阶段（3-4 天）

| 阶段 | 时间 | 任务 |
|------|------|------|
| **Phase 1** | 1 天 | 创建数据库表 + 基础 API |
| **Phase 2** | 1 天 | 完善业务逻辑 + 重试机制 |
| **Phase 3** | 1 天 | HEARTBEAT 集成 + 测试 |
| **Phase 4** | 1 天 | 部署 + 监控 |

---

### 5.2 Phase 1 详细任务

| 任务 | 说明 |
|------|------|
| 在 hope05:53306 创建表 | 执行 `bot_tables_simple.sql` |
| 创建 FastAPI 项目结构 | 目录结构、配置文件 |
| 实现 Task 模型 | SQLAlchemy 模型 |
| 实现基础 CRUD API | GET/POST/PUT/DELETE |
| 实现 API Key 认证 | 中间件验证 |

---

### 5.3 Phase 2 详细任务

| 任务 | 说明 |
|------|------|
| 实现状态流转逻辑 | pending → running → completed/failed |
| 实现重试机制 | 失败任务自动重试 |
| 实现进度更新 | progress 字段更新 |
| 实现审计日志查询 | 获取任务日志 API |
| 实现统计视图 | 今日任务统计 |

---

### 5.4 Phase 3 详细任务

| 任务 | 说明 |
|------|------|
| 修改 HEARTBEAT.md | 各容器集成 API 调用 |
| 测试任务分发流程 | Hope 创建任务 → anna 执行 |
| 测试跨容器协作 | trump 完成 → cc 接手 |
| 测试重试机制 | 失败任务自动重试 |
| 测试优先级排序 | P0 > P1 > P2 |

---

### 5.5 Phase 4 详细任务

| 任务 | 说明 |
|------|------|
| Docker 部署 | Dockerfile + docker-compose |
| systemd 服务 | 创建 systemd 服务文件 |
| 监控告警 | 任务失败告警 |
| 文档完善 | README + API 文档 |

---

## 6. 部署方案

### 6.1 Docker 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot-todolist:
    build: .
    ports:
      - "8090:8090"
    environment:
      - DB_HOST=hope05
      - DB_PORT=53306
      - DB_USER=root
      - DB_PASSWORD=Tianfs@2020!!
      - DB_NAME=hope_engine
      - API_KEY=hope-bot-apikey-2026-0424
    restart: unless-stopped
```

### 6.2 systemd 服务

```ini
# /etc/systemd/system/bot-todolist.service
[Unit]
Description=Bot TodoList Service
After=network.target

[Service]
Type=simple
User=hope
WorkingDirectory=/Users/hope/hope-bot-service
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8090
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 7. 监控与告警

### 7.1 监控指标

| 指标 | 说明 |
|------|------|
| **pending_tasks_count** | 待执行任务数量 |
| **running_tasks_count** | 执行中任务数量 |
| **failed_tasks_count** | 失败任务数量 |
| **avg_task_duration** | 平均任务耗时 |
| **success_rate** | 成功率 |

### 7.2 告警规则

| 规则 | 说明 |
|------|------|
| P0 任务失败 | 立即通知用户 |
| pending 任务积压 | 超过 10 个待执行任务，通知用户 |
| 失败率过高 | 失败率 > 20%，通知用户 |
| bot 离线 | 超过 1 小时无任务执行，通知用户 |

---

## 8. 总结

### 8.1 极简版优势

| 优势 | 说明 |
|------|------|
| **快速上线** | 3-4 天完成开发 |
| **易于维护** | 2 张表，23 个字段 |
| **聚焦核心** | 任务分发 + 进度跟踪 + 审计日志 |
| **灵活扩展** | task_params JSON 格式，可扩展 |

### 8.2 后期扩展（可选）

| 扩展 | 说明 |
|------|------|
| **任务模板** | 后期需要时再加 bot_task_template 表 |
| **任务评论** | 后期需要时再加 bot_task_comment 表 |
| **统计分析** | 用 SQL 查询代替，后期可加定时任务 |

---

## 9. 文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| **极简版 SQL** | `~/hope-bot/sql/bot_tables_simple.sql` | 数据库表结构 |
| **设计文档** | `~/hope-bot/docs/bot-service-design-simple.md` | 本文档 |
| **HEARTBEAT 模板** | `~/hope-bot/templates/HEARTBEAT-bot-api.md` | HEARTBEAT 集成模板 |

---

**设计完成时间：2026-04-24 19:36**
**开发预计时间：3-4 天**
**部署预计时间：1 天**