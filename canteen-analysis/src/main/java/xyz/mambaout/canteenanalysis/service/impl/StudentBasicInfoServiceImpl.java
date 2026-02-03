package xyz.mambaout.canteenanalysis.service.impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataScore;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudent;
import xyz.mambaout.canteenanalysis.entity.query.BasicQuery;
import xyz.mambaout.canteenanalysis.mapper.BasicDataStudentMapper;
import xyz.mambaout.canteenanalysis.service.IStudentBasicInfoService;

import java.util.List;

/**
 * 学生基础信息服务实现：分页查询、详情与成绩操作。
 */
@Service
@Slf4j
public class StudentBasicInfoServiceImpl implements IStudentBasicInfoService {
    @Autowired
    private BasicDataStudentMapper studentMapper;
    /**
     * 分页查询学生基础信息。
     */
    @Override
    public PageResult<BasicDataStudent> getStudentInfo(BasicQuery studentquery) {
        Integer pageNum = studentquery.getPage() == null || studentquery.getPage() < 1 ? 1 : studentquery.getPage();
        Integer pageSize = studentquery.getPageSize() == null || studentquery.getPageSize() < 1 ? 20 : studentquery.getPageSize();

        PageHelper.startPage(pageNum, pageSize);
        Page<BasicDataStudent> page =(Page<BasicDataStudent>) studentMapper.getStudentInfo(studentquery);
        PageResult<BasicDataStudent> pageResult = new PageResult<>();
        pageResult.setCode(0);
        pageResult.setMsg("success");
        pageResult.setTotal(page.getTotal());
        pageResult.setPage(page.getPageNum());
        pageResult.setPageSize(page.getPageSize());
        pageResult.setRecords(page.getResult());
        return pageResult;
    }

    /**
     * 获取学生成绩列表。
     */
    @Override
    public List<BasicDataScore> getStudentScore(String studentId) {
        log.info("getStudentScore: {}", studentId);
        return studentMapper.getStudentScore(studentId);
    }

    /**
     * 获取学生详情。
     */
    @Override
    public BasicDataStudent getStudentDetail(String studentId) {
        log.info("getStudentDetail: {}", studentId);
        return studentMapper.getStudentDetail(studentId);
    }

    /**
     * 新增学生。
     */
    @Override
    public boolean addStudent(BasicDataStudent student) {
        if (student == null || student.getStudentId() == null || student.getStudentId().isBlank()) {
            return false;
        }
        return studentMapper.addStudent(student) > 0;
    }

    /**
     * 更新学生信息。
     */
    @Override
    public boolean updateStudent(String studentId, BasicDataStudent student) {
        if (student == null || studentId == null || studentId.isBlank()) {
            return false;
        }
        student.setStudentId(studentId);
        return studentMapper.updateStudent(student) > 0;
    }

    /**
     * 删除学生。
     */
    @Override
    public boolean deleteStudent(String studentId) {
        if (studentId == null || studentId.isBlank()) {
            return false;
        }
        return studentMapper.deleteStudent(studentId) > 0;
    }

    /**
     * 导出学生基础信息（不分页）。
     */
    @Override
    public List<BasicDataStudent> exportStudentInfo(BasicQuery studentquery) {
        return studentMapper.getStudentInfo(studentquery);
    }
}
