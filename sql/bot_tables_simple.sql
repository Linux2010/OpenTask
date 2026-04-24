-- Bot TodoList 数据库表结构（极简版）
-- 创建时间：2026-04-24 19:35
-- 数据库：hope_engine
-- 位置：hope05:53306
-- 设计原则：保留核心功能，删除过度设计

-- =============================================
-- 1. 任务表（核心表）- 极简版
-- =============================================

CREATE TABLE `bot_task` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  
  -- 基本信息
  `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
  `task_description` TEXT DEFAULT NULL COMMENT '任务描述',
  `task_params` TEXT DEFAULT NULL COMMENT '任务参数（JSON格式，包含所有参数/步骤/输入输出）',
  
  -- 分配与优先级
  `assigned_to` VARCHAR(50) NOT NULL COMMENT '分配对象（trump/cc/anna/main/session_agent）',
  `priority` VARCHAR(10) NOT NULL DEFAULT 'P2' COMMENT '优先级（P0紧急/P1重要/P2一般）',
  
  -- 状态与进度
  `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态（pending/running/completed/failed/cancelled）',
  `progress` INT(11) DEFAULT 0 COMMENT '执行进度（0-100）',
  
  -- 时间信息
  `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `started_time` DATETIME DEFAULT NULL COMMENT '开始时间',
  `completed_time` DATETIME DEFAULT NULL COMMENT '完成时间',
  
  -- 执行结果
  `result` TEXT DEFAULT NULL COMMENT '执行结果',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  
  -- 重试机制
  `retry_count` INT(11) DEFAULT 0 COMMENT '已重试次数',
  `max_retry` INT(11) DEFAULT 3 COMMENT '最大重试次数',
  
  -- 创建者
  `created_by` VARCHAR(50) NOT NULL COMMENT '创建者（hope/manual）',
  
  -- 删除标记
  `deleted` TINYINT(1) DEFAULT 0 COMMENT '是否删除',
  
  -- 更新时间
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  INDEX `idx_assigned_to` (`assigned_to`),
  INDEX `idx_status` (`status`),
  INDEX `idx_priority` (`priority`),
  INDEX `idx_assigned_status` (`assigned_to`, `status`),
  INDEX `idx_created_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bot任务表（极简版）';

-- =============================================
-- 2. 任务日志表（审计日志）- 极简版
-- =============================================

CREATE TABLE `bot_task_log` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `task_id` BIGINT(20) NOT NULL COMMENT '任务ID',
  
  -- 动作信息
  `action` VARCHAR(50) NOT NULL COMMENT '动作（created/started/completed/failed/retried/cancelled）',
  `message` TEXT DEFAULT NULL COMMENT '日志信息',
  
  -- 状态变更
  `old_status` VARCHAR(20) DEFAULT NULL COMMENT '原状态',
  `new_status` VARCHAR(20) DEFAULT NULL COMMENT '新状态',
  
  -- 操作者
  `operator` VARCHAR(50) DEFAULT NULL COMMENT '操作者',
  
  -- 时间
  `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  INDEX `idx_task_id` (`task_id`),
  INDEX `idx_action` (`action`),
  INDEX `idx_created_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bot任务日志表（极简版）';

-- =============================================
-- 3. 触发器（自动记录日志）
-- =============================================

DELIMITER //

-- 任务创建时记录日志
CREATE TRIGGER `tr_bot_task_created` 
AFTER INSERT ON `bot_task`
FOR EACH ROW
BEGIN
  INSERT INTO `bot_task_log` (
    `task_id`, `action`, `message`, `new_status`, `operator`, `created_time`
  )
  VALUES (
    NEW.id, 'created', 
    CONCAT('创建任务：', NEW.task_name, '，分配给 ', NEW.assigned_to),
    NEW.status, NEW.created_by, NOW()
  );
END//

-- 任务状态变更时记录日志
CREATE TRIGGER `tr_bot_task_status_change` 
AFTER UPDATE ON `bot_task`
FOR EACH ROW
BEGIN
  IF OLD.status != NEW.status THEN
    INSERT INTO `bot_task_log` (
      `task_id`, `action`, `message`, `old_status`, `new_status`, `operator`, `created_time`
    )
    VALUES (
      NEW.id,
      CASE NEW.status 
        WHEN 'running' THEN 'started'
        WHEN 'completed' THEN 'completed'
        WHEN 'failed' THEN 'failed'
        WHEN 'cancelled' THEN 'cancelled'
        ELSE 'status_changed'
      END,
      CONCAT('状态变更：', OLD.status, ' → ', NEW.status),
      OLD.status, NEW.status, NEW.assigned_to, NOW()
    );
  END IF;
END//

DELIMITER ;

-- =============================================
-- 4. 视图（常用查询）
-- =============================================

-- 待执行任务视图（按优先级排序）
CREATE OR REPLACE VIEW `v_bot_pending` AS
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

-- 今日任务统计视图
CREATE OR REPLACE VIEW `v_bot_today_stats` AS
SELECT 
  assigned_to,
  COUNT(*) as total,
  SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
  SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM bot_task
WHERE deleted = 0 AND DATE(created_time) = CURDATE()
GROUP BY assigned_to;

-- =============================================
-- 5. 示例数据
-- =============================================

-- 示例任务
INSERT INTO `bot_task` (
  `task_name`, `task_description`, `task_params`, 
  `assigned_to`, `priority`, `status`, `created_by`
) VALUES
(
  '给老板打招呼',
  '发送祝福语到 Telegram',
  '{"telegram_id":"5520269161","message":"老板早上好！今天天气不错，祝您心情愉快！","steps":["检查连接","发送消息","确认成功"]}',
  'anna', 'P1', 'pending', 'hope'
),
(
  '检查 hope02 上传状态',
  '检查 Bilibili 上传引擎运行状态',
  '{"server":"hope02","platform":"bili","check_logs":true}',
  'trump', 'P0', 'pending', 'hope'
),
(
  '测试西瓜视频发布',
  '使用 Playwright 测试西瓜视频自动发布',
  '{"platform":"xigua","test_video":"/tmp/test.mp4"}',
  'trump', 'P2', 'pending', 'hope'
);

-- =============================================
-- 6. 完成
-- =============================================

-- 验证表创建
SELECT TABLE_NAME, TABLE_COMMENT 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'hope_engine' AND TABLE_NAME LIKE 'bot_%';