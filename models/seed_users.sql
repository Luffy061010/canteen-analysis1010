-- models/seed_users.sql
-- 示例用户种子（由脚本生成模板）
-- 运行方法：在项目根目录运行 `python scripts/generate_users.py --count 100 --start 100001 --password-mode username`

INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100001', SHA2('100001', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100002', SHA2('100002', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100003', SHA2('100003', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100004', SHA2('100004', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100005', SHA2('100005', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100006', SHA2('100006', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100007', SHA2('100007', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100008', SHA2('100008', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100009', SHA2('100009', 256), 0, 1, NOW());
INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES ('100010', SHA2('100010', 256), 0, 1, NOW());
