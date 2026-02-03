package xyz.mambaout.canteenanalysis.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface SystemStatusMapper {
    @Select("SELECT COUNT(1) FROM basic_data_student")
    Long countStudents();

    @Select("SELECT IFNULL(SUM(amount), 0) FROM consumption_data_students_consumption WHERE DATE(consumption_time) = CURDATE()")
    Double sumTodayConsumption();

    @Select("SELECT IFNULL(SUM(amount), 0) FROM consumption_data_students_consumption WHERE DATE_FORMAT(consumption_time, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')")
    Double sumMonthlyConsumption();
}