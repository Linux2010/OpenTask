-- OpenTask Lite - SQLite 表结构
-- 极简版：2 张表，无触发器（SQLite 不支持复杂触发器）

-- =============================================
-- 1. 任务表（核心表）
-- =============================================

CREATE TABLE IF NOT EXISTS bot_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本信息
    task_name TEXT NOT NULL,
    task_description TEXT,
    task_params TEXT,              -- JSON 格式参数

    -- 分配与优先级
    assigned_to TEXT NOT NULL,     -- 目标 agent（默认当前 agent）
    priority TEXT DEFAULT 'P2',    -- P0 紧急 / P1 重要 / P2 一般

    -- 状态与进度
    status TEXT DEFAULT 'pending', -- pending/running/completed/failed/cancelled
    progress INTEGER DEFAULT 0,    -- 0-100

    -- 时间信息
    created_time TEXT DEFAULT CURRENT_TIMESTAMP,
    started_time TEXT,
    completed_time TEXT,

    -- 执行结果
    result TEXT,
    error_message TEXT,

    -- 重试机制
    retry_count INTEGER DEFAULT 0,
    max_retry INTEGER DEFAULT 3,

    -- 创建者
    created_by TEXT,

    -- 删除标记
    deleted INTEGER DEFAULT 0
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_task_assigned_to ON bot_task(assigned_to);
CREATE INDEX IF NOT EXISTS idx_task_status ON bot_task(status);
CREATE INDEX IF NOT EXISTS idx_task_priority ON bot_task(priority);

-- =============================================
-- 2. 任务日志表（审计日志）
-- =============================================

CREATE TABLE IF NOT EXISTS bot_task_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,

    -- 动作信息
    action TEXT NOT NULL,          -- created/started/completed/failed/retried/cancelled
    message TEXT,

    -- 状态变更
    old_status TEXT,
    new_status TEXT,

    -- 操作者
    operator TEXT,

    -- 时间
    created_time TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_log_task_id ON bot_task_log(task_id);
CREATE INDEX IF NOT EXISTS idx_log_action ON bot_task_log(action);

-- =============================================
-- 3. 视图（SQLite 支持）
-- =============================================

-- 待执行任务视图（按优先级排序）
CREATE VIEW IF NOT EXISTS v_pending_tasks AS
SELECT
    id, task_name, task_description, assigned_to, priority, status,
    progress, created_time, task_params
FROM bot_task
WHERE deleted = 0 AND status = 'pending'
ORDER BY
    CASE priority
        WHEN 'P0' THEN 0
        WHEN 'P1' THEN 1
        WHEN 'P2' THEN 2
        ELSE 3
    END,
    created_time ASC;

-- 今日统计视图
CREATE VIEW IF NOT EXISTS v_today_stats AS
SELECT
    assigned_to,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM bot_task
WHERE deleted = 0 AND DATE(created_time) = DATE('now', 'localtime')
GROUP BY assigned_to;