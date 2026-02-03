package xyz.mambaout.canteenanalysis.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import xyz.mambaout.canteenanalysis.entity.dto.LogDeleteRequest;
import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.SystemLog;
import xyz.mambaout.canteenanalysis.entity.query.LogQuery;
import xyz.mambaout.canteenanalysis.service.ISystemLogService;
import xyz.mambaout.canteenanalysis.entity.vo.SystemLogStatsVO;

import java.nio.charset.StandardCharsets;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 系统日志查询、统计与导出接口。
 */
@RestController
@RequestMapping("/system")
@Slf4j
public class SystemLogController {
    @Autowired
    private ISystemLogService systemLogService;

    /**
     * 分页查询系统日志。
     */
    @GetMapping("/logs")
    public PageResult<SystemLog> getSystemLogs(LogQuery query) {
        log.info("getSystemLogs: {}", query);
        return systemLogService.queryLogs(query);
    }

    /**
     * 获取日志统计信息。
     */
    @GetMapping("/logs/stats")
    public SystemLogStatsVO getSystemLogStats(LogQuery query) {
        log.info("getSystemLogStats: {}", query);
        return systemLogService.stats(query);
    }

    /**
     * 导出日志为 CSV。
     */
    @GetMapping("/logs/export")
    public ResponseEntity<byte[]> exportSystemLogs(LogQuery query) {
        log.info("exportSystemLogs: {}", query);
        List<SystemLog> logs = systemLogService.exportLogs(query);
        String header = "id,operationTime,operator,operationType,module,operationDetail,ipAddress,result,executionTime\n";
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        String body = logs.stream().map(l -> String.join(",",
                safe(l.getId()),
                safe(l.getOperationTime() == null ? null : l.getOperationTime().format(formatter)),
                safe(l.getOperator()),
                safe(l.getOperationType()),
                safe(l.getModule()),
                safe(l.getOperationDetail()),
                safe(l.getIpAddress()),
                safe(l.getResult()),
                safe(l.getExecutionTime())
        )).collect(Collectors.joining("\n"));

        byte[] bytes = (header + body).getBytes(StandardCharsets.UTF_8);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=system_logs.csv")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(bytes);
    }

    /**
     * 批量删除日志。
     */
    @DeleteMapping("/logs")
    public Map<String, Object> deleteSystemLogs(@RequestBody LogDeleteRequest request) {
        boolean ok = systemLogService.deleteLogs(request.getLogIds());
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 0 : 1);
        resp.put("msg", ok ? "success" : "fail");
        return resp;
    }

    /**
     * CSV 字段安全转义。
     */
    private String safe(Object val) {
        if (val == null) return "";
        String s = String.valueOf(val);
        // Escape quotes and commas by wrapping in quotes
        if (s.contains(",") || s.contains("\"") || s.contains("\n")) {
            s = s.replace("\"", "\"\"");
            return "\"" + s + "\"";
        }
        return s;
    }
}