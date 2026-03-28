-- Indexes for consumption queries and student filters.
-- This script is safe to rerun and won't fail if tables/indexes are missing.

DELIMITER $$
CREATE PROCEDURE ensure_index(
	IN p_table VARCHAR(128),
	IN p_index VARCHAR(128),
	IN p_cols VARCHAR(255),
	IN p_unique TINYINT
)
BEGIN
	IF EXISTS (
			SELECT 1
			FROM information_schema.tables
			WHERE table_schema = DATABASE()
				AND table_name = p_table
		) AND NOT EXISTS (
			SELECT 1
			FROM information_schema.statistics
			WHERE table_schema = DATABASE()
				AND table_name = p_table
				AND index_name = p_index
		) THEN
		SET @sql = CONCAT(
			'CREATE ', IF(p_unique = 1, 'UNIQUE ', ''),
			'INDEX ', p_index, ' ON ', p_table, ' (', p_cols, ')'
		);
		PREPARE stmt FROM @sql;
		EXECUTE stmt;
		DEALLOCATE PREPARE stmt;
	END IF;
END$$
DELIMITER ;

CALL ensure_index('consumption_data_students_consumption', 'idx_consumption_student_time', 'student_id, consumption_time', 0);
CALL ensure_index('consumption_data_students_consumption', 'idx_consumption_time', 'consumption_time', 0);
CALL ensure_index('basic_data_student', 'idx_student_college', 'college', 0);
CALL ensure_index('basic_data_student', 'idx_student_major', 'major', 0);
CALL ensure_index('basic_data_student', 'idx_student_grade', 'grade', 0);
CALL ensure_index('basic_data_student', 'idx_student_class', 'class_name', 0);
CALL ensure_index('basic_data_student', 'idx_student_id', 'student_id', 1);

DROP PROCEDURE ensure_index;
