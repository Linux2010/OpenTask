-- Bot Configuration Table
CREATE TABLE IF NOT EXISTS bot_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bot_name VARCHAR(50) NOT NULL UNIQUE COMMENT 'Bot identifier',
    display_name VARCHAR(100) COMMENT 'Display name for UI',
    description VARCHAR(500) COMMENT 'Bot description',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether bot is available for assignment',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Available bots configuration';

-- Insert default bots
INSERT INTO bot_config (bot_name, display_name, description) VALUES
('main', 'Main Bot', 'Primary mission control bot'),
('trump', 'Trump Bot', 'Dedicated Trump analysis bot'),
('cc', 'CC Bot', 'Claude Code assistant bot'),
('anna', 'Anna Bot', 'Session agent bot'),
('session_agent', 'Session Agent', 'Dynamic session agent')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name);