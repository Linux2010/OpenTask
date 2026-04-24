# Bot TodoList - AI Agent Task Distribution System

> A lightweight task distribution system for managing multiple OpenClaw bot containers
> 
> **极简设计**：2 张表，23 个字段，专注核心功能

---

## 🎯 What is Bot TodoList?

Bot TodoList is a **task distribution system** designed for managing multiple OpenClaw bot containers:

- **Hope (main)** - Central task dispatcher
- **trump** - Upload engine operator
- **cc** - Claude Code container
- **anna** - Testing/operations container

**Key Problem Solved**: Mission Control uses SQLite (local database), which causes **data isolation** - each container has its own database and cannot share tasks. Bot TodoList uses **MySQL (remote database)** to enable cross-container task distribution.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ✅ **Task Distribution** | Assign tasks to specific bots (assigned_to field) |
| ✅ **Priority Queue** | P0 (urgent) > P1 (important) > P2 (normal) |
| ✅ **Progress Tracking** | Real-time progress updates (0-100%) |
| ✅ **Task Parameters** | JSON format with flexible structure (task_params) |
| ✅ **Audit Logs** | Automatic status change tracking (bot_task_log) |
| ✅ **Retry Mechanism** | Failed tasks auto-retry (max_retry) |
| ✅ **Soft Delete** | Deleted tasks marked, not removed |
| ✅ **REST API** | FastAPI endpoints for task management |

---

## 🗄️ Database Design (Minimal)

### 2 Tables Only

| Table | Fields | Description |
|-------|--------|-------------|
| **bot_task** | 16 | Core task table |
| **bot_task_log** | 7 | Audit log table |

### bot_task Fields

```
id, task_name, task_description, task_params (JSON)
assigned_to, priority (P0/P1/P2)
status (pending/running/completed/failed/cancelled), progress
created_time, started_time, completed_time
result, error_message
retry_count, max_retry
created_by, deleted, update_time
```

### Task Status Flow

```
pending → running → completed
                   ↘ failed → (retry) → running
                   ↘ cancelled
```

---

## 🚀 Quick Start

### 1. Create Database Tables

```bash
# Connect to MySQL
mysql -h hope05 -P 53306 -u root -p'Tianfs@2020!!' hope_engine

# Execute SQL
source sql/bot_tables_simple.sql
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

### 4. Test API

```bash
# Get pending tasks for anna
curl -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=anna"

# Create a task
curl -X POST -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks" \
  -d '{"task_name":"给老板打招呼","assigned_to":"anna","priority":"P1"}'
```

---

## 🔧 Configuration

### Database

| Config | Value |
|--------|-------|
| **Host** | hope05 |
| **Port** | 53306 |
| **Database** | hope_engine |
| **User** | root |
| **Password** | Tianfs@2020!! |

### API

| Config | Value |
|--------|-------|
| **API Key** | `hope-bot-apikey-2026-0424` |
| **Header** | `X-Bot-Key` |
| **Port** | 8090 |

---

## 📂 Project Structure

```
bot-todolist/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose
├── .env                         # Environment variables
├── sql/
│   └── bot_tables_simple.sql    # Database schema (2 tables)
├── docs/
│   └ bot-service-design-simple.md # Design document
│   └── HEARTBEAT-bot-api.md     # HEARTBEAT integration guide
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration
│   ├── models/
│   │   ├── task.py              # Task model
│   │   └── task_log.py          # TaskLog model
│   ├── routers/
│   │   └── task.py              # Task API routes
│   ├── services/
│   │   └── task_service.py      # Business logic
│   ├── utils/
│   │   ├── db.py                # Database connection
│   │   └ auth.py                # API Key authentication
│   └── schemas/
│       ├── task.py              # Pydantic models
│       └── response.py          # Response models
└── tests/
    ├── test_task_api.py         # API tests
    └── test_task_service.py     # Service tests
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List tasks (filterable) |
| `/api/tasks` | POST | Create task |
| `/api/tasks/{id}` | GET | Get task detail |
| `/api/tasks/{id}` | PUT | Update task |
| `/api/tasks/{id}` | DELETE | Delete task (soft) |
| `/api/tasks/pending` | GET | Get pending tasks by bot |
| `/api/tasks/{id}/start` | PUT | Start task execution |
| `/api/tasks/{id}/complete` | PUT | Mark task completed |
| `/api/tasks/{id}/fail` | PUT | Mark task failed |
| `/api/tasks/{id}/retry` | PUT | Retry failed task |
| `/api/tasks/{id}/cancel` | PUT | Cancel task |
| `/api/stats/today` | GET | Today's statistics |
| `/api/logs/{task_id}` | GET | Get task logs |

---

## 🤖 Bot Identity

| Bot | assigned_to | Description |
|-----|-------------|-------------|
| **Hope (main)** | main | Central dispatcher |
| **trump** | trump | Upload engine operator |
| **cc** | cc | Claude Code container |
| **anna** | anna | Testing/operations |

---

## 🔄 HEARTBEAT Integration

Each OpenClaw container checks for pending tasks during heartbeat:

```bash
# Get pending tasks
curl -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=anna"

# Start execution
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/start"

# Complete task
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/complete" \
  -d '{"result":"执行成功"}'
```

See `docs/HEARTBEAT-bot-api.md` for full integration guide.

---

## 📊 Why Not Mission Control?

**Mission Control (OpenClaw skill) uses SQLite local database:**

| Container | Database Path | Data |
|-----------|---------------|------|
| main | ~/.openclaw/mission-control.db | ❌ Isolated |
| trump | ~/.openclaw-trump/mission-control.db | ❌ Isolated |
| cc | ~/.openclaw-cc/mission-control.db | ❌ Isolated |
| anna | ~/.openclaw-anna/mission-control.db | ❌ Isolated |

**Result**: Containers cannot share tasks - main cannot assign tasks to trump/cc/anna!

**Bot TodoList Solution**: MySQL remote database (hope05:53306) - all containers share the same task queue!

---

## 🛠️ Development Roadmap

| Phase | Time | Tasks |
|-------|------|-------|
| **Phase 1** | 1 day | Create tables + Basic API |
| **Phase 2** | 1 day | Business logic + Retry mechanism |
| **Phase 3** | 1 day | HEARTBEAT integration + Testing |
| **Phase 4** | 1 day | Deployment + Monitoring |

---

## 📝 License

MIT License - Open Source

---

## 👤 Author

- **Hope** - AI Assistant
- **Andy** - Project Owner

---

## 🔗 Related Projects

- [Mission Control](https://github.com/alanxurox/mission-control) - OpenClaw agent fleets coordination (SQLite-based)
- [hope-bot](https://github.com/Linux2010/hope-bot) - Bot TodoList design documents

---

**Version**: v1.0
**Created**: 2026-04-24
**Status**: Design Complete, Development Pending