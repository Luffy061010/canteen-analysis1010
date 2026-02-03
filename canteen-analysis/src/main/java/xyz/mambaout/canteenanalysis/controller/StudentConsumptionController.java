package xyz.mambaout.canteenanalysis.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudentsConsumption;
import xyz.mambaout.canteenanalysis.entity.query.TimeQuery;
import xyz.mambaout.canteenanalysis.entity.vo.ConsumptionCompareVO;
import xyz.mambaout.canteenanalysis.entity.vo.SimpleConsumptionStatVO;
import xyz.mambaout.canteenanalysis.entity.vo.TopWindowStatVO;
import xyz.mambaout.canteenanalysis.service.IStudentConsumptionService;

import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 学生消费相关接口：明细、统计、窗口分布与对比。
 */
@Slf4j
@RestController
@RequestMapping("/consumption_data")
public class StudentConsumptionController {
    @Autowired
    private IStudentConsumptionService consumptionService;
    /**
     * 查询学生消费明细（分页）。
     */
    @GetMapping("/StudentConsumption")
    public PageResult<BasicDataStudentsConsumption> getStudentConsumption(TimeQuery timeQuery) {
        log.info("getStudentConsumption params: {}", timeQuery);
        return consumptionService.queryStudentComsumption(timeQuery);
    }
    /**
     * 查询消费汇总统计。
     */
    @GetMapping("/StudentConsumptionStat")
    public SimpleConsumptionStatVO simpleConsumptionStat(TimeQuery timeQuery) {
        log.info("simpleConsumptionStat params: {}", timeQuery);
        return consumptionService.simpleConsumptionStat(timeQuery);
    }
    /**
     * 窗口消费 Top 分布（用于柱状/饼图）。
     */
    @GetMapping("/window/top/barAndPie")
    public TopWindowStatVO topWindowStat(TimeQuery timeQuery) {
        log.info("topWindowStat params: {}", timeQuery);
        return consumptionService.topWindowStat(timeQuery);
    }
    /**
     * 消费对比统计。
     */
    @GetMapping("/compare")
    public ConsumptionCompareVO consumptionCompareStat(TimeQuery timeQuery) {
        log.info("consumptionCompareStat params: {}", timeQuery);
        return consumptionService.consumptionCompareStat(timeQuery);
    }

    /**
     * 导出消费明细 CSV（不分页）。
     */
    @GetMapping("/StudentConsumption/export")
    public ResponseEntity<byte[]> exportStudentConsumption(TimeQuery timeQuery) {
        log.info("exportStudentConsumption params: {}", timeQuery);
        List<BasicDataStudentsConsumption> records = consumptionService.exportStudentConsumption(timeQuery);
        String header = "studentId,name,college,major,className,grade,consumptionTime,amount,windowId,mealType\n";
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        String body = records.stream().map(r -> String.join(",",
                safe(r.getStudentId()),
                safe(r.getName()),
                safe(r.getCollege()),
                safe(r.getMajor()),
                safe(r.getClassName()),
                safe(r.getGrade()),
                safe(r.getConsumptionTime() == null ? null : r.getConsumptionTime().format(formatter)),
                safe(r.getAmount()),
                safe(r.getWindowId()),
                safe(r.getMealType())
        )).collect(Collectors.joining("\n"));

        byte[] bytes = (header + body).getBytes(StandardCharsets.UTF_8);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=consumption.csv")
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
