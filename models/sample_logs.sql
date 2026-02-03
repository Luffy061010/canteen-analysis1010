-- 插入一些示例日志（假设 admin 的 id 是 1）
-- 在执行前请确认 user.id 对应正确的用户

INSERT INTO `log` (user_id, username, action, detail, created_at) VALUES
(1, 'admin', 'register', 'seed admin user', NOW()),
(1, 'admin', 'login', 'seed login', NOW()),
(1, 'admin', 'add_user', '添加示例用户 user1', NOW());
