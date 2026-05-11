# OpenTask Lite 命令文档

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENTASK_DB` | `skills/opentask/data/db.sqlite3` | 数据库路径 |
| `OPENTASK_AGENT` | Runtime `agent` 或 `main` | 当前 agent 标识 |

---

## 全局选项

**注意：全局选项必须在子命令之前。**

```bash
python opentask.py --format=table pending
# 不是 python opentask.py pending --format=table
```

| 选项 | 说明 |
|------|------|
| `--format=json` | JSON 输出（默认） |
| `--format=table` | 表格输出 |

---

## 命令列表

### init - 初始化数据库

```bash
python opentask.py init
```

创建数据库文件和表结构。

---

### pending - 获取待执行任务

```bash
python opentask.py pending
python opentask.py pending --format=table
```

获取分配给当前 agent 的待执行任务，按优先级排序 (P0 > P1 > P2)。

**返回示例：**
```json
[
  {
    "id": 1,
    "task_name": "紧急任务",
    "priority": "P0",
    "assigned_to": "main",
    "status": "pending",
    "created_time": "2026-05-11T10:00:00"
  }
]
```

---

### list - 列出任务

```bash
python opentask.py list
python opentask.py list --agent=anna
python opentask.py list --status=completed
python opentask.py list --priority=P0
```

**参数：**
| 参数 | 说明 |
|------|------|
| `--agent` | 按 agent 筛选 |
| `--status` | 按状态筛选 |
| `--priority` | 按优先级筛选 |

---

### show - 任务详情

```bash
python opentask.py show <id>
```

获取任务详情，包含所有字段和操作日志。

**返回示例：**
```json
{
  "id": 1,
  "task_name": "发送消息",
  "task_params": "{\"telegram_id\":\"xxx\"}",
  "status": "completed",
  "result": "消息已发送",
  "logs": [
    {"action": "created", "created_time": "..."},
    {"action": "started", "old_status": "pending", "new_status": "running"},
    {"action": "completed", "old_status": "running", "new_status": "completed"}
  ]
}
```

---

### stats - 今日统计

```bash
python opentask.py stats
```

获取今日各 agent 的任务统计。

**返回示例：**
```json
[
  {
    "assigned_to": "main",
    "total": 10,
    "pending": 2,
    "running": 1,
    "completed": 6,
    "failed": 1
  }
]
```

---

### create - 创建任务

```bash
python opentask.py create <name>
python opentask.py create <name> --to=<agent>
python opentask.py create <name> --priority=P0
python opentask.py create <name> --desc="描述"
python opentask.py create <name> --params='{"key":"value"}'
```

**参数：**
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `name` | 必填 | 任务名称 |
| `--to` | 当前 agent | 分配目标 |
| `--priority` | P2 | 优先级 P0/P1/P2 |
| `--desc` | - | 任务描述 |
| `--params` | - | 任务参数（JSON） |

---

### start - 开始执行

```bash
python opentask.py start <id>
```

将 pending 任务状态改为 running。

---

### complete - 完成任务

```bash
python opentask.py complete <id>
python opentask.py complete <id> --result="执行成功"
```

将 running 任务状态改为 completed。

---

### fail - 标记失败

```bash
python opentask.py fail <id>
python opentask.py fail <id> --error="连接超时"
```

将 running 任务状态改为 failed。

---

### retry - 重试失败任务

```bash
python opentask.py retry <id>
```

将 failed 任务状态改为 pending，并增加 retry_count。

**限制：** 最大重试次数为 `max_retry`（默认 3 次）。

---

### cancel - 取消任务

```bash
python opentask.py cancel <id>
```

将 pending 或 running 任务状态改为 cancelled。

---

### delete - 删除任务

```bash
python opentask.py delete <id>
```

软删除任务（设置 deleted=1）。

---

## 任务状态流程

```
pending → running → completed
                   ↘ failed → (retry) → pending
                   ↘ cancelled
```

---

## 在 HEARTBEAT 中使用

```bash
# 检查是否有待执行任务
TASKS=$(python opentask.py pending)

# 解析第一条任务 ID
TASK_ID=$(echo "$TASKS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')")

if [ -n "$TASK_ID" ]; then
    # 开始执行
    python opentask.py start $TASK_ID

    # 执行任务逻辑...

    # 完成任务
    python opentask.py complete $TASK_ID --result="完成"
else
    echo "HEARTBEAT_OK"
fi
```