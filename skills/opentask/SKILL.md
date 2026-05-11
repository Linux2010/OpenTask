---
name: opentask
description: OpenTask Lite - 轻量级任务管理。查询和管理任务，支持多 agent 共享数据库。使用场景：(1) 查询待执行任务、获取任务列表、任务详情；(2) 创建任务、开始执行、完成任务、标记失败、重试、取消；(3) 查看今日统计。触发短语："查询任务"、"获取任务"、"创建任务"、"完成任务"、"opentask"、"任务管理"。
---

# opentask Skill

轻量级任务管理系统，无需 HTTP 服务，直接操作 SQLite 数据库。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENTASK_DB` | `skills/opentask/data/db.sqlite3` | 数据库路径 |
| `OPENTASK_AGENT` | `main` | 当前 agent 标识 |

---

## Agent 标识

- 默认分配给自己（`OPENTASK_AGENT`）
- 可通过 `--to` 参数分配给其他 agent
- 多 agent 共享：设置相同 `OPENTASK_DB` 路径

---

## 快速使用

### 初始化

```bash
python skills/opentask/opentask.py init
```

### 查询

```bash
python skills/opentask/opentask.py pending              # 待执行任务
python skills/opentask/opentask.py list --status=pending
python skills/opentask/opentask.py show 1               # 任务详情
python skills/opentask/opentask.py stats                # 今日统计
```

### 创建

```bash
python skills/opentask/opentask.py create "任务名"
python skills/opentask/opentask.py create "任务名" --to=anna --priority=P1
python skills/opentask/opentask.py create "任务名" --params='{"key":"value"}'
```

### 执行

```bash
python skills/opentask/opentask.py start 1
python skills/opentask/opentask.py complete 1 --result="成功"
python skills/opentask/opentask.py fail 1 --error="失败原因"
python skills/opentask/opentask.py retry 1
python skills/opentask/opentask.py cancel 1
```

---

## 输出格式

```bash
python skills/opentask/opentask.py --format=table pending
```

| 格式 | 说明 |
|------|------|
| `json`（默认） | JSON 格式 |
| `table` | 表格格式 |

---

## Priority

| 值 | 说明 |
|------|------|
| `P0` | 紧急 |
| `P1` | 重要 |
| `P2` | 一般 |

---

## Status

| 值 | 说明 |
|------|------|
| `pending` | 待执行 |
| `running` | 执行中 |
| `completed` | 已完成 |
| `failed` | 失败 |
| `cancelled` | 已取消 |

---

## 详细文档

- [api.md](references/api.md) - 完整命令文档
- [schema.sql](schema.sql) - 数据库表结构