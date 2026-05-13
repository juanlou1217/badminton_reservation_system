-- 体育馆羽毛球预约系统初始化脚本
-- 一次性完成：建表、默认系统设置、演示场地、当天演示时间段。
-- 管理员账号建议使用 `python scripts/init_admin.py` 创建，避免在公开 SQL 中固定密码。

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    status VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_username (username),
    CONSTRAINT chk_users_role CHECK (role IN ('user', 'admin')),
    CONSTRAINT chk_users_status CHECK (status IN ('normal', 'disabled'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS courts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    court_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    remark VARCHAR(255) NOT NULL DEFAULT '',
    INDEX idx_courts_court_no (court_no),
    CONSTRAINT chk_courts_status CHECK (status IN ('open', 'closed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS time_slots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    court_id INT NOT NULL,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    CONSTRAINT fk_time_slots_court FOREIGN KEY (court_id) REFERENCES courts(id),
    CONSTRAINT uq_time_slots_court_date_time UNIQUE (court_id, slot_date, start_time, end_time),
    CONSTRAINT chk_time_slots_status CHECK (status IN ('available', 'booked', 'disabled')),
    CONSTRAINT chk_time_slots_time_range CHECK (start_time < end_time),
    INDEX idx_time_slots_court_id (court_id),
    INDEX idx_time_slots_slot_date (slot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reservations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    reservation_no VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    court_id INT NOT NULL,
    slot_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'booked',
    active_slot_id INT GENERATED ALWAYS AS (
        CASE WHEN status = 'booked' THEN slot_id ELSE NULL END
    ) STORED,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    cancelled_at DATETIME NULL,
    CONSTRAINT fk_reservations_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_reservations_court FOREIGN KEY (court_id) REFERENCES courts(id),
    CONSTRAINT fk_reservations_slot FOREIGN KEY (slot_id) REFERENCES time_slots(id),
    CONSTRAINT uq_reservations_active_slot UNIQUE (active_slot_id),
    CONSTRAINT chk_reservations_status CHECK (status IN ('booked', 'cancelled', 'finished')),
    INDEX idx_reservations_user_id (user_id),
    INDEX idx_reservations_court_id (court_id),
    INDEX idx_reservations_slot_id (slot_id),
    INDEX idx_reservations_no (reservation_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(50) NOT NULL UNIQUE,
    setting_value VARCHAR(255) NOT NULL,
    remark TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO settings (setting_key, setting_value, remark)
VALUES
    ('max_daily_reservations', '2', '单个用户每天最多预约次数'),
    ('announcement', '欢迎使用体育馆羽毛球预约系统。', '系统公告')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), remark = VALUES(remark);

INSERT INTO courts (court_no, name, location, status, remark)
VALUES
    ('C01', '一号场', '体育馆一层东侧', 'open', '演示数据'),
    ('C02', '二号场', '体育馆一层西侧', 'open', '演示数据'),
    ('C03', '三号场', '体育馆二层', 'open', '演示数据')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    location = VALUES(location),
    status = VALUES(status),
    remark = VALUES(remark);

INSERT INTO time_slots (court_id, slot_date, start_time, end_time, status)
SELECT c.id, CURDATE(), t.start_time, t.end_time, 'available'
FROM courts c
JOIN (
    SELECT TIME('08:00:00') AS start_time, TIME('10:00:00') AS end_time
    UNION ALL SELECT TIME('10:00:00'), TIME('12:00:00')
    UNION ALL SELECT TIME('14:00:00'), TIME('16:00:00')
    UNION ALL SELECT TIME('16:00:00'), TIME('18:00:00')
) t
WHERE c.court_no IN ('C01', 'C02', 'C03')
ON DUPLICATE KEY UPDATE status = time_slots.status;
