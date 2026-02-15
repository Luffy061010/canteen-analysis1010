-- 用户表 SQL
CREATE TABLE IF NOT EXISTS user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 默认管理员账号：lin / 061010
INSERT INTO user (username, password_hash, is_admin, is_active)
VALUES ('lin', 'fe7533d0af1cebb8d70ecda6723cf5255e5a6bda4b440781e4b94771a8cda694', 1, 1)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    is_admin = 1,
    is_active = 1;
