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
ON DUPLICATE KEY UPDATE name = VALUES(name), location = VALUES(location), status = VALUES(status), remark = VALUES(remark);
