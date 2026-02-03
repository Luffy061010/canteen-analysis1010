package xyz.mambaout.canteenanalysis.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Update;
import org.apache.ibatis.annotations.Delete;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataScore;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudent;
import xyz.mambaout.canteenanalysis.entity.query.BasicQuery;

import java.util.List;

@Mapper
public interface BasicDataStudentMapper {
    List<BasicDataStudent> getStudentInfo(BasicQuery studentquery);

    @Select("SELECT student_id AS studentId, grade, college, major, name, class_name AS className, gender, phone_number AS phoneNumber FROM basic_data_student WHERE student_id = #{studentId} LIMIT 1")
    BasicDataStudent getStudentDetail(String studentId);

    @Insert("INSERT INTO basic_data_student (student_id, grade, college, major, name, class_name, gender, phone_number) VALUES (#{studentId}, #{grade}, #{college}, #{major}, #{name}, #{className}, #{gender}, #{phoneNumber})")
    int addStudent(BasicDataStudent student);

    @Update("UPDATE basic_data_student SET grade = #{grade}, college = #{college}, major = #{major}, name = #{name}, class_name = #{className}, gender = #{gender}, phone_number = #{phoneNumber} WHERE student_id = #{studentId}")
    int updateStudent(BasicDataStudent student);

    @Delete("DELETE FROM basic_data_student WHERE student_id = #{studentId}")
    int deleteStudent(String studentId);

    @Select("SELECT * FROM basic_data_score WHERE student_id = #{studentId}")
    List<BasicDataScore> getStudentScore(String studentId);
}
