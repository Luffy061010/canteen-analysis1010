-- Seed: add student 202401010101 and corresponding user account
-- 使用方法：在 MySQL 客户端或脚本中执行此文件（确保使用正确的数据库）

-- 如果 basic_data_student 表中尚无该学号，则插入学生基础信息（使用 INSERT IGNORE 避免重复错误）
INSERT IGNORE INTO basic_data_student (student_id, name, college, major, class_name, grade)
VALUES ('202401010101', '张三', '计算机学院', '软件工程', '软件一班', '2024');

-- 在 user 表中插入对应账号，密码为 123456（使用 SHA-256 存储）
INSERT IGNORE INTO `user` (username, password_hash, is_admin, is_active, created_at)
VALUES ('202401010101', SHA2('123456', 256), 0, 1, NOW());
