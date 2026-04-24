# HEARTBEAT.md - Bot TodoList API 集成

> **Bot 任务检查模板**
> 
> 用于 OpenClaw 容器 heartbeat 时调用 Bot TodoList API

---

## API 配置

| 配置项 | 值 |
|--------|-----|
| **API 地址** | `http://hope05:8090/api` |
| **API Key** | `hope-bot-apikey-2026-0424` |
| **请求头** | `X-Bot-Key: hope-bot-apikey-2026-0424` |

---

## 心跳流程

1. 调用 API 获取待执行任务（按优先级排序）
2. 如果有 **P0 任务**，立即执行并通知用户
3. 如果有 **P1 任务**，按顺序执行
4. 如果有 **P2 任务**，有时间时执行
5. 执行完成后，调用 API 更新状态

---

## API 命令示例

### 获取待执行任务

```bash
# 获取 anna 的待执行任务
curl -s -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=anna"

# 获取 trump 的待执行任务
curl -s -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=trump"

# 获取 cc 的待执行任务
curl -s -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=cc"

# 获取 main 的待执行任务
curl -s -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=main"
```

### 开始执行任务

```bash
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/start"
```

### 更新进度

```bash
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1" \
  -d '{"progress":50}'
```

### 完成任务

```bash
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/complete" \
  -d '{"result":"执行成功：已发送消息到 Telegram"}'
```

### 标记失败

```bash
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/fail" \
  -d '{"error_message":"Telegram 连接失败"}'
```

### 重试任务

```bash
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/retry"
```

### 取消任务

```bash
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/1/cancel"
```

---

## 任务状态说明

| 状态 | 说明 | 操作 |
|------|------|------|
| **pending** | 待执行 | 调用 `/start` 开始执行 |
| **running** | 执行中 | 调用 `/complete` 或 `/fail` |
| **completed** | 已完成 | 无需操作 |
| **failed** | 失败 | 调用 `/retry` 重试或 `/cancel` 取消 |
| **cancelled** | 已取消 | 无需操作 |

---

## 优先级说明

| 优先级 | 说明 | 处理方式 |
|--------|------|----------|
| **P0** | 紧急 | 立即执行，通知用户 |
| **P1** | 重要 | 按顺序执行 |
| **P2** | 一般 | 有时间时执行 |

---

## 响应格式

### 任务列表响应

```json
[
  {
    "id": 1,
    "task_name": "给老板打招呼",
    "task_description": "发送祝福语到 Telegram",
    "task_params": "{\"telegram_id\":\"5520269161\",\"message\":\"老板早上好！\"}",
    "assigned_to": "anna",
    "priority": "P1",
    "status": "pending",
    "progress": 0,
    "created_time": "2026-04-24 19:36:00"
  }
]
```

### 单个任务响应

```json
{
  "id": 1,
  "task_name": "给老板打招呼",
  "status": "running",
  "progress": 50,
  "started_time": "2026-04-24 19:37:00"
}
```

---

## 今日任务统计

```bash
curl -s -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/stats/today"
```

### 统计响应

```json
{
  "anna": {
    "total": 5,
    "pending": 2,
    "running": 1,
    "completed": 2,
    "failed": 0
  },
  "trump": {
    "total": 3,
    "pending": 1,
    "completed": 2,
    "failed": 0
  }
}
```

---

## Bot 身份标识

| Bot | assigned_to 值 | 说明 |
|------|----------------|------|
| **主实例** | `main` | Hope 主实例 |
| **trump 容器** | `trump` | 上传引擎运维 |
| **cc 容器** | `cc` | Claude Code 容器 |
| **anna 容器** | `anna` | 测试/运营容器 |

---

## 错误处理

### API 调用失败

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| **401** | API Key 无效 | 检查 X-Bot-Key 请求头 |
| **404** | 任务不存在 | 检查任务 ID |
| **500** | 服务内部错误 | 检查日志，联系管理员 |

### 任务执行失败

1. 调用 `/fail` 标记失败
2. 记录 error_message
3. 如果 retry_count < max_retry，调用 `/retry` 重试
4. 如果重试次数已达上限，通知用户

---

## 示例：完整的任务执行流程

```bash
# 1. 获取待执行任务
TASKS=$(curl -s -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/pending?assigned_to=anna")

# 2. 解析第一个任务
TASK_ID=$(echo $TASKS | jq -r '.[0].id')
TASK_NAME=$(echo $TASKS | jq -r '.[0].task_name')

# 3. 开始执行
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/$TASK_ID/start"

# 4. 执行任务逻辑（根据 task_params）
# ... 执行具体任务 ...

# 5. 完成任务
curl -X PUT -H "X-Bot-Key: hope-bot-apikey-2026-0424" \
  "http://hope05:8090/api/tasks/$TASK_ID/complete" \
  -d '{"result":"执行成功"}'
```

---

**文档版本：v1.0**
**创建时间：2026-04-24 19:36**