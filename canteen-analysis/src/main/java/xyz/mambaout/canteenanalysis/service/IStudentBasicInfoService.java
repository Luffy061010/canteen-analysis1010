package xyz.mambaout.canteenanalysis.service;


import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataScore;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudent;
import xyz.mambaout.canteenanalysis.entity.query.BasicQuery;

import java.util.List;

/**
 * 学生基础信息服务接口。
 */
public interface IStudentBasicInfoService {
    /**
     * 分页查询学生基础信息。
     */
    PageResult<BasicDataStudent> getStudentInfo(BasicQuery studentquery);

    /**
     * 获取学生成绩。
     */
    List<BasicDataScore> getStudentScore(String studentId);

    /**
     * 获取学生详情。
     */
    BasicDataStudent getStudentDetail(String studentId);

    /**
     * 新增学生。
     */
    boolean addStudent(BasicDataStudent student);

    /**
     * 更新学生。
     */
    boolean updateStudent(String studentId, BasicDataStudent student);

    /**
     * 删除学生。
     */
    boolean deleteStudent(String studentId);

    /**
     * 导出学生基础信息（不分页）。
     */
    List<BasicDataStudent> exportStudentInfo(BasicQuery studentquery);
}
