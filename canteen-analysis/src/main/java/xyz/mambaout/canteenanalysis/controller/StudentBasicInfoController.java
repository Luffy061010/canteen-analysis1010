package xyz.mambaout.canteenanalysis.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataScore;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudent;
import xyz.mambaout.canteenanalysis.entity.query.BasicQuery;
import xyz.mambaout.canteenanalysis.service.IStudentBasicInfoService;

import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;

/**
 * 学生基础信息与成绩相关接口。
 */
@RestController
@Slf4j
@RequestMapping("/basic_data")
public class StudentBasicInfoController {
    @Autowired
    private IStudentBasicInfoService studentBasicInfoService;

    /**
     * 查询学生基础信息（支持条件筛选与分页）。
     */
    @GetMapping("/student/info")
    public PageResult<BasicDataStudent> getStudentInfo(BasicQuery studentquery) {
        log.info("getStudentInfo: {}", studentquery);
        return studentBasicInfoService.getStudentInfo(studentquery);
    }

    /**
     * 学生列表（与 student/info 复用查询逻辑）。
     */
    @GetMapping("/student/list")
    public PageResult<BasicDataStudent> getStudentList(BasicQuery studentquery) {
        log.info("getStudentList: {}", studentquery);
        return studentBasicInfoService.getStudentInfo(studentquery);
    }

    /**
     * 获取单个学生详情。
     */
    @GetMapping("/student/detail/{studentId}")
    public BasicDataStudent getStudentDetail(@PathVariable String studentId) {
        log.info("getStudentDetail: {}", studentId);
        return studentBasicInfoService.getStudentDetail(studentId);
    }

    /**
     * 新增学生。
     */
    @PostMapping("/student/add")
    public Map<String, Object> addStudent(@RequestBody BasicDataStudent student) {
        log.info("addStudent: {}", student);
        boolean ok = studentBasicInfoService.addStudent(student);
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 0 : 1);
        resp.put("msg", ok ? "success" : "fail");
        return resp;
    }

    /**
     * 更新学生信息。
     */
    @PutMapping("/student/update/{studentId}")
    public Map<String, Object> updateStudent(@PathVariable String studentId, @RequestBody BasicDataStudent student) {
        log.info("updateStudent: {}, body={}", studentId, student);
        boolean ok = studentBasicInfoService.updateStudent(studentId, student);
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 0 : 1);
        resp.put("msg", ok ? "success" : "fail");
        return resp;
    }

    /**
     * 删除学生。
     */
    @DeleteMapping("/student/delete/{studentId}")
    public Map<String, Object> deleteStudent(@PathVariable String studentId) {
        log.info("deleteStudent: {}", studentId);
        boolean ok = studentBasicInfoService.deleteStudent(studentId);
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 0 : 1);
        resp.put("msg", ok ? "success" : "fail");
        return resp;
    }
    /**
     * 查询学生成绩列表。
     */
    @GetMapping("/student/score")
    public List<BasicDataScore> getStudentScore(String studentId) {
        return studentBasicInfoService.getStudentScore(studentId);
    }

    /**
     * 导出学生基础信息 CSV。
     */
    @GetMapping("/student/export")
    public ResponseEntity<byte[]> exportStudents(BasicQuery studentquery) {
        log.info("exportStudents: {}", studentquery);
        List<BasicDataStudent> students = studentBasicInfoService.exportStudentInfo(studentquery);
        String header = "studentId,grade,college,major,name,className,gender,phoneNumber\n";
        String body = students.stream().map(s -> String.join(",",
                safe(s.getStudentId()),
                safe(s.getGrade()),
                safe(s.getCollege()),
                safe(s.getMajor()),
                safe(s.getName()),
                safe(s.getClassName()),
                safe(s.getGender()),
                safe(s.getPhoneNumber())
        )).collect(Collectors.joining("\n"));

        byte[] bytes = (header + body).getBytes(StandardCharsets.UTF_8);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=students.csv")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(bytes);
    }

    private String safe(Object val) {
        if (val == null) return "";
        String s = String.valueOf(val);
        if (s.contains(",") || s.contains("\"") || s.contains("\n")) {
            s = s.replace("\"", "\"\"");
            return "\"" + s + "\"";
        }
        return s;
    }
}
