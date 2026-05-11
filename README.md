# OpenTask - AI Agent Task Distribution System

> A lightweight, open-source task distribution system for managing multiple OpenClaw bot containers
> 
> **极简设计**：2 张表，23 个字段，专注核心功能

---

## 🎯 What is OpenTask?

OpenTask is an **open-source task distribution system** designed for managing multiple OpenClaw bot containers.

**Key Problem Solved**: Mission Control uses SQLite (local database), which causes **data isolation** - each container has its own database and cannot share tasks. OpenTask uses **MySQL (remote database)** to enable cross-container task distribution.

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
| ✅ **Web UI** | HTMX + Jinja2 admin dashboard |

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
# Connect to MySQL (use your own credentials)
mysql -h <HOST> -P <PORT> -u <USER> -p hope_engine

# Execute SQL
source sql/bot_tables_simple.sql
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
DB_HOST=<your_db_host>
DB_PORT=<your_db_port>
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_NAME=hope_engine
API_KEY=<your_api_key>
API_PREFIX=/api
```

### 4. Run Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

### 5. Test API

```bash
# Get pending tasks
curl -H "X-Bot-Key: <your_api_key>" \
  "http://localhost:8090/api/tasks/pending?assigned_to=anna"

# Create a task
curl -X POST -H "X-Bot-Key: <your_api_key>" \
  "http://localhost:8090/api/tasks" \
  -d '{"task_name":"示例任务","assigned_to":"anna","priority":"P1"}'
```

---

## 🔧 Configuration

All configuration is read from `.env` file via pydantic-settings.

| Config | Description |
|--------|-------------|
| `DB_HOST` | MySQL host |
| `DB_PORT` | MySQL port |
| `DB_USER` | MySQL user |
| `DB_PASSWORD` | MySQL password |
| `DB_NAME` | Database name |
| `API_KEY` | API authentication key |
| `API_PREFIX` | API route prefix |

---

## 📂 Project Structure

```
opentask/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose
├── .env                         # Environment variables
├── sql/
│   └── bot_tables_simple.sql    # Database schema
│   └── bot_config.sql           # Bot config table
├── docs/
│   └── bot-service-design-simple.md
│   └── HEARTBEAT-bot-api.md
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration
│   ├── htmx/                    # HTMX Web UI routes
│   ├── templates/               # Jinja2 templates
│   ├── routers/                 # API routes
│   ├── services/                # Business logic
│   ├── utils/                   # Helpers
│   └── schemas/                 # Pydantic models
└── tests/
    ├── test_task_api.py
    └── ui/                      # Playwright UI tests
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

## 🌐 Web UI

Access at `http://localhost:8090/web/`

| Page | Path | Description |
|------|------|-------------|
| Dashboard | `/web/` | Today stats, quick actions |
| Tasks List | `/web/tasks` | Filterable task table |
| Bot Management | `/web/bots` | Active bots overview |
| Create Task | `/web/tasks/new` | Quick task form |
| Task Detail | `/web/tasks/{id}` | Status operations, logs |

---

## 🔄 HEARTBEAT Integration

Each OpenClaw container checks for pending tasks during heartbeat:

```bash
# Get pending tasks
curl -H "X-Bot-Key: <your_api_key>" \
  "http://<host>:8090/api/tasks/pending?assigned_to=<bot_name>"

# Start execution
curl -X PUT -H "X-Bot-Key: <your_api_key>" \
  "http://<host>:8090/api/tasks/{id}/start"

# Complete task
curl -X PUT -H "X-Bot-Key: <your_api_key>" \
  "http://<host>:8090/api/tasks/{id}/complete" \
  -d '{"result":"执行成功"}'
```

See `docs/HEARTBEAT-bot-api.md` for full integration guide.

---

## 📊 Why Not Mission Control?

**Mission Control (OpenClaw skill) uses SQLite local database:**

| Container | Database | Shared? |
|-----------|----------|---------|
| main | ~/.openclaw/mission-control.db | ❌ Isolated |
| trump | ~/.openclaw-trump/mission-control.db | ❌ Isolated |
| cc | ~/.openclaw-cc/mission-control.db | ❌ Isolated |
| anna | ~/.openclaw-anna/mission-control.db | ❌ Isolated |

**OpenTask Solution**: MySQL remote database - all containers share the same task queue!

---

## 📝 License

MIT License - Open Source

---

## 🔗 Related Projects

- [Mission Control](https://github.com/alanxurox/mission-control) - OpenClaw agent fleets coordination (SQLite-based)
- [hope-bot](https://github.com/Linux2010/hope-bot) - OpenTask design documents

---

**Version**: v1.0