-- Minimal business tables to avoid 500 errors when DB is empty.
-- This script only creates structure; analytics still need real data import.

CREATE TABLE IF NOT EXISTS basic_data_student (
    student_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NULL,
    college VARCHAR(128) NULL,
    major VARCHAR(128) NULL,
    class_name VARCHAR(128) NULL,
    grade VARCHAR(32) NULL
);

CREATE TABLE IF NOT EXISTS consumption_data_students_consumption (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(32) NOT NULL,
    consumption_time DATETIME NOT NULL,
    window_id VARCHAR(64) NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    meal_type VARCHAR(16) NULL,
    INDEX idx_consumption_student_time (student_id, consumption_time),
    INDEX idx_consumption_time (consumption_time)
);

CREATE TABLE IF NOT EXISTS basic_data_score (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(32) NOT NULL,
    term VARCHAR(32) NOT NULL,
    gpa DECIMAL(5,2) NULL,
    INDEX idx_score_student_term (student_id, term)
);
