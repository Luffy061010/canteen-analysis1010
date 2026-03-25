package xyz.mambaout.canteenanalysis.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface SystemStatusMapper {
    @Select("SELECT COUNT(1) FROM basic_data_student")
    Long countStudents();

    @Select("SELECT IFNULL(SUM(amount), 0) FROM consumption_data_students_consumption WHERE consumption_time >= CURDATE() AND consumption_time < DATE_ADD(CURDATE(), INTERVAL 1 DAY)")
    Double sumTodayConsumption();

    @Select("SELECT IFNULL(SUM(amount), 0) FROM consumption_data_students_consumption WHERE consumption_time >= DATE_FORMAT(CURDATE(), '%Y-%m-01') AND consumption_time < DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH)")
    Double sumMonthlyConsumption();
}