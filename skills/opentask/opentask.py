#!/usr/bin/env python3
"""
OpenTask Lite - 轻量级任务管理脚本

直接操作 SQLite 数据库，无需 HTTP 服务。
支持多 agent 共享数据库（通过 OPENTASK_DB 环境变量指定路径）。

使用方式：
    python opentask.py pending              # 获取待执行任务
    python opentask.py create "任务名"       # 创建任务
    python opentask.py complete 1           # 完成任务
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# =============================================
# 配置
# =============================================

def get_db_path() -> Path:
    """获取数据库路径"""
    db_path = os.environ.get('OPENTASK_DB')
    if db_path:
        return Path(db_path)
    # 默认路径：脚本所在目录的 data/db.sqlite3
    script_dir = Path(__file__).parent
    return script_dir / 'data' / 'db.sqlite3'


def get_agent_name() -> str:
    """获取当前 agent 标识"""
    # 优先级：环境变量 > 默认值
    agent = os.environ.get('OPENTASK_AGENT')
    if agent:
        return agent
    return 'main'


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================
# 初始化
# =============================================

def init_db():
    """初始化数据库"""
    conn = get_connection()
    schema_path = Path(__file__).parent / 'schema.sql'
    if schema_path.exists():
        with open(schema_path) as f:
            conn.executescript(f.read())
    else:
        # 内嵌 schema
        conn.executescript(SCHEMA_SQL)
    conn.close()
    output_json({'status': 'ok', 'message': f'数据库初始化完成: {get_db_path()}'})


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS bot_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    task_description TEXT,
    task_params TEXT,
    assigned_to TEXT NOT NULL,
    priority TEXT DEFAULT 'P2',
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    created_time TEXT DEFAULT CURRENT_TIMESTAMP,
    started_time TEXT,
    completed_time TEXT,
    result TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retry INTEGER DEFAULT 3,
    created_by TEXT,
    deleted INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_task_assigned_to ON bot_task(assigned_to);
CREATE INDEX IF NOT EXISTS idx_task_status ON bot_task(status);
CREATE INDEX IF NOT EXISTS idx_task_priority ON bot_task(priority);

CREATE TABLE IF NOT EXISTS bot_task_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    message TEXT,
    old_status TEXT,
    new_status TEXT,
    operator TEXT,
    created_time TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_log_task_id ON bot_task_log(task_id);
"""


# =============================================
# 日志记录
# =============================================

def add_log(conn, task_id: int, action: str, old_status: str = None,
            new_status: str = None, message: str = None, operator: str = None):
    """记录任务日志"""
    conn.execute("""
        INSERT INTO bot_task_log (task_id, action, old_status, new_status, message, operator)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task_id, action, old_status, new_status, message, operator or get_agent_name()))


# =============================================
# 输出格式
# =============================================

def output_json(data: Any):
    """JSON 格式输出"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def output_table(rows: List[Dict], headers: List[str]):
    """表格格式输出"""
    if not rows:
        print("无数据")
        return

    # 计算列宽
    widths = [len(h) for h in headers]
    for row in rows:
        for i, h in enumerate(headers):
            val = str(row.get(h, '') or '')
            widths[i] = max(widths[i], len(val))

    # 打印表头
    header_line = ' | '.join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print('-' * len(header_line))

    # 打印数据
    for row in rows:
        line = ' | '.join(str(row.get(h, '') or '').ljust(w) for h, w in zip(headers, widths))
        print(line)


# =============================================
# 查询操作
# =============================================

def get_pending(format: str = 'json'):
    """获取待执行任务（当前 agent）"""
    agent = get_agent_name()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM bot_task
        WHERE deleted = 0 AND status = 'pending' AND assigned_to = ?
        ORDER BY
            CASE priority
                WHEN 'P0' THEN 0
                WHEN 'P1' THEN 1
                WHEN 'P2' THEN 2
                ELSE 3
            END,
            created_time ASC
    """, (agent,)).fetchall()
    conn.close()

    tasks = [dict(row) for row in rows]
    if format == 'table':
        output_table(tasks, ['id', 'task_name', 'priority', 'assigned_to', 'created_time'])
    else:
        output_json(tasks)


def list_tasks(agent: str = None, status: str = None, priority: str = None, format: str = 'json'):
    """列出任务"""
    conn = get_connection()
    sql = "SELECT * FROM bot_task WHERE deleted = 0"
    params = []

    if agent:
        sql += " AND assigned_to = ?"
        params.append(agent)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if priority:
        sql += " AND priority = ?"
        params.append(priority)

    sql += " ORDER BY created_time DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    tasks = [dict(row) for row in rows]
    if format == 'table':
        output_table(tasks, ['id', 'task_name', 'status', 'priority', 'assigned_to', 'created_time'])
    else:
        output_json(tasks)


def show_task(task_id: int, format: str = 'json'):
    """获取任务详情"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ? AND deleted = 0", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        return

    task = dict(row)

    # 获取日志
    logs = conn.execute("""
        SELECT * FROM bot_task_log WHERE task_id = ? ORDER BY created_time DESC
    """, (task_id,)).fetchall()
    task['logs'] = [dict(log) for log in logs]

    conn.close()

    if format == 'table':
        print(f"\n任务 #{task_id}")
        print(f"名称: {task['task_name']}")
        print(f"状态: {task['status']}")
        print(f"优先级: {task['priority']}")
        print(f"分配给: {task['assigned_to']}")
        print(f"创建时间: {task['created_time']}")
        if task['task_description']:
            print(f"描述: {task['task_description']}")
        if task['task_params']:
            print(f"参数: {task['task_params']}")
        if task['result']:
            print(f"结果: {task['result']}")
        if task['error_message']:
            print(f"错误: {task['error_message']}")
        print(f"\n日志 ({len(task['logs'])} 条):")
        output_table(task['logs'], ['action', 'old_status', 'new_status', 'message', 'created_time'])
    else:
        output_json(task)


def get_stats(format: str = 'json'):
    """获取今日统计"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            assigned_to,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM bot_task
        WHERE deleted = 0 AND DATE(created_time) = DATE('now', 'localtime')
        GROUP BY assigned_to
    """).fetchall()
    conn.close()

    stats = [dict(row) for row in rows]
    if format == 'table':
        output_table(stats, ['assigned_to', 'total', 'pending', 'running', 'completed', 'failed'])
    else:
        output_json(stats)


# =============================================
# 操作命令
# =============================================

def create_task(task_name: str, assigned_to: str = None, priority: str = 'P2',
                description: str = None, params: str = None):
    """创建任务"""
    agent = get_agent_name()
    target = assigned_to or agent  # 默认给自己

    conn = get_connection()
    now = datetime.now().isoformat()
    cursor = conn.execute("""
        INSERT INTO bot_task (task_name, task_description, task_params, assigned_to, priority, created_by, created_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (task_name, description, params, target, priority, agent, now))

    task_id = cursor.lastrowid
    add_log(conn, task_id, 'created', None, 'pending', f'创建任务: {task_name}', agent)
    conn.commit()

    # 获取创建的任务
    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    conn.close()

    output_json(dict(row))


def start_task(task_id: int):
    """开始执行任务"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ? AND deleted = 0", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        conn.close()
        return

    task = dict(row)
    if task['status'] != 'pending':
        output_json({'error': f'任务状态不允许启动: {task["status"]}'})
        conn.close()
        return

    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE bot_task SET status = 'running', started_time = ?, progress = 0
        WHERE id = ?
    """, (now, task_id))

    add_log(conn, task_id, 'started', 'pending', 'running', '任务开始执行', get_agent_name())
    conn.commit()

    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    output_json(dict(row))


def complete_task(task_id: int, result: str = None):
    """完成任务"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ? AND deleted = 0", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        conn.close()
        return

    task = dict(row)
    if task['status'] != 'running':
        output_json({'error': f'任务状态不允许完成: {task["status"]}'})
        conn.close()
        return

    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE bot_task SET status = 'completed', completed_time = ?, progress = 100, result = ?
        WHERE id = ?
    """, (now, result, task_id))

    add_log(conn, task_id, 'completed', 'running', 'completed', result or '任务完成', get_agent_name())
    conn.commit()

    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    output_json(dict(row))


def fail_task(task_id: int, error: str = None):
    """标记任务失败"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ? AND deleted = 0", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        conn.close()
        return

    task = dict(row)
    if task['status'] != 'running':
        output_json({'error': f'任务状态不允许标记失败: {task["status"]}'})
        conn.close()
        return

    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE bot_task SET status = 'failed', completed_time = ?, error_message = ?
        WHERE id = ?
    """, (now, error, task_id))

    add_log(conn, task_id, 'failed', 'running', 'failed', error or '任务失败', get_agent_name())
    conn.commit()

    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    output_json(dict(row))


def retry_task(task_id: int):
    """重试失败任务"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ? AND deleted = 0", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        conn.close()
        return

    task = dict(row)
    if task['status'] != 'failed':
        output_json({'error': f'只能重试失败的任务: {task["status"]}'})
        conn.close()
        return

    if task['retry_count'] >= task['max_retry']:
        output_json({'error': f'已达到最大重试次数: {task["retry_count"]}/{task["max_retry"]}'})
        conn.close()
        return

    conn.execute("""
        UPDATE bot_task
        SET status = 'pending', started_time = NULL, completed_time = NULL,
            error_message = NULL, retry_count = retry_count + 1
        WHERE id = ?
    """, (task_id,))

    add_log(conn, task_id, 'retried', 'failed', 'pending',
            f'重试次数: {task["retry_count"] + 1}', get_agent_name())
    conn.commit()

    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    output_json(dict(row))


def cancel_task(task_id: int):
    """取消任务"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ? AND deleted = 0", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        conn.close()
        return

    task = dict(row)
    if task['status'] not in ('pending', 'running'):
        output_json({'error': f'只能取消待执行或执行中的任务: {task["status"]}'})
        conn.close()
        return

    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE bot_task SET status = 'cancelled', completed_time = ?
        WHERE id = ?
    """, (now, task_id))

    add_log(conn, task_id, 'cancelled', task['status'], 'cancelled', '任务取消', get_agent_name())
    conn.commit()

    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    output_json(dict(row))


def delete_task(task_id: int):
    """删除任务（软删除）"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
    if not row:
        output_json({'error': f'任务不存在: {task_id}'})
        conn.close()
        return

    conn.execute("UPDATE bot_task SET deleted = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    output_json({'id': task_id, 'deleted': True})


# =============================================
# CLI 入口
# =============================================

def main():
    parser = argparse.ArgumentParser(description='OpenTask Lite - 轻量级任务管理')
    parser.add_argument('--format', choices=['json', 'table'], default='json', help='输出格式')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # init
    subparsers.add_parser('init', help='初始化数据库')

    # pending
    subparsers.add_parser('pending', help='获取待执行任务（当前 agent）')

    # list
    list_parser = subparsers.add_parser('list', help='列出任务')
    list_parser.add_argument('--agent', help='按 agent 筛选')
    list_parser.add_argument('--status', help='按状态筛选')
    list_parser.add_argument('--priority', help='按优先级筛选')

    # show
    show_parser = subparsers.add_parser('show', help='获取任务详情')
    show_parser.add_argument('id', type=int, help='任务 ID')

    # stats
    subparsers.add_parser('stats', help='今日统计')

    # create
    create_parser = subparsers.add_parser('create', help='创建任务')
    create_parser.add_argument('name', help='任务名称')
    create_parser.add_argument('--to', help='分配给（默认当前 agent）')
    create_parser.add_argument('--priority', default='P2', help='优先级 P0/P1/P2')
    create_parser.add_argument('--desc', help='任务描述')
    create_parser.add_argument('--params', help='任务参数（JSON 格式）')

    # start
    start_parser = subparsers.add_parser('start', help='开始执行任务')
    start_parser.add_argument('id', type=int, help='任务 ID')

    # complete
    complete_parser = subparsers.add_parser('complete', help='完成任务')
    complete_parser.add_argument('id', type=int, help='任务 ID')
    complete_parser.add_argument('--result', help='执行结果')

    # fail
    fail_parser = subparsers.add_parser('fail', help='标记任务失败')
    fail_parser.add_argument('id', type=int, help='任务 ID')
    fail_parser.add_argument('--error', help='错误信息')

    # retry
    retry_parser = subparsers.add_parser('retry', help='重试失败任务')
    retry_parser.add_argument('id', type=int, help='任务 ID')

    # cancel
    cancel_parser = subparsers.add_parser('cancel', help='取消任务')
    cancel_parser.add_argument('id', type=int, help='任务 ID')

    # delete
    delete_parser = subparsers.add_parser('delete', help='删除任务')
    delete_parser.add_argument('id', type=int, help='任务 ID')

    args = parser.parse_args()

    # 执行命令
    if args.command == 'init':
        init_db()
    elif args.command == 'pending':
        get_pending(args.format)
    elif args.command == 'list':
        list_tasks(args.agent, args.status, args.priority, args.format)
    elif args.command == 'show':
        show_task(args.id, args.format)
    elif args.command == 'stats':
        get_stats(args.format)
    elif args.command == 'create':
        create_task(args.name, args.to, args.priority, args.desc, args.params)
    elif args.command == 'start':
        start_task(args.id)
    elif args.command == 'complete':
        complete_task(args.id, args.result)
    elif args.command == 'fail':
        fail_task(args.id, args.error)
    elif args.command == 'retry':
        retry_task(args.id)
    elif args.command == 'cancel':
        cancel_task(args.id)
    elif args.command == 'delete':
        delete_task(args.id)


if __name__ == '__main__':
    main()