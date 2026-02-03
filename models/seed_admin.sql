-- 在 MySQL 中插入初始管理员账号
-- 请先确认 `user` 表已存在
-- 修改 'adminpass' 为你想要的初始密码

INSERT INTO `user` (username, password_hash, is_admin, is_active)
VALUES ('admin', SHA2('adminpass', 256), 1, 1);

-- 如果你需要指定 created_at（可选）：
-- INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at)
-- VALUES ('admin', SHA2('adminpass',256), 1, 1, NOW());
