# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenTask is a FastAPI-based task distribution system for managing multiple OpenClaw bot containers. It solves the data isolation problem where Mission Control uses SQLite (local per-container databases) by using a centralized MySQL database that all containers share.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8090

# Run with Docker
docker-compose up -d

# Run tests
pytest tests/

# Database setup (first time)
mysql -h hope05 -P 53306 -u root -p hope_engine < sql/bot_tables_simple.sql
```

## Architecture

### Layered Structure
- **Routers** (`app/routers/`): FastAPI endpoints, request validation, HTTP responses
- **Services** (`app/services/`): Business logic, database operations, task state management
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation
- **Models** (`app/models/`): SQLAlchemy table definitions (reference only, not used for queries)
- **Utils** (`app/utils/`): Database connection helpers, API key authentication

### Database Layer
Uses raw pymysql queries via helper functions in [db.py](app/utils/db.py):
- `execute_query()` - SELECT queries, returns dict rows
- `execute_insert()` - INSERT, returns lastrowid
- `execute_update()` - UPDATE/DELETE, returns affected rows

Connection config is in [config.py](app/config.py) via pydantic-settings, reads from `.env`.

### Task State Machine
```
pending → running → completed
                   ↘ failed → (retry) → pending
                   ↘ cancelled
```

### Two Tables
- `bot_task`: Core task data (16 fields) - id, task_name, assigned_to, priority, status, progress, timestamps, result, retry_count
- `bot_task_log`: Audit log (7 fields) - tracks all status changes with timestamps

### API Authentication
All `/api/*` endpoints require `X-Bot-Key` header matching `API_KEY` in config. See [auth.py](app/utils/auth.py).

## Key Design Notes

- Soft delete: tasks marked `deleted=1`, not removed from database
- Priority ordering: P0 (urgent) > P1 (important) > P2 (normal)
- Retry limit: max 3 retries (`max_retry` field)
- Task logs recorded both by application and MySQL triggers (see [bot_tables_simple.sql](sql/bot_tables_simple.sql))

## Bot Identity Values

The `assigned_to` field values: `main`, `trump`, `cc`, `anna`, `session_agent`