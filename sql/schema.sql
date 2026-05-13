CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    status VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS courts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    court_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    remark VARCHAR(255) NOT NULL DEFAULT '',
    INDEX idx_courts_court_no (court_no)
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    cancelled_at DATETIME NULL,
    CONSTRAINT fk_reservations_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_reservations_court FOREIGN KEY (court_id) REFERENCES courts(id),
    CONSTRAINT fk_reservations_slot FOREIGN KEY (slot_id) REFERENCES time_slots(id),
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
