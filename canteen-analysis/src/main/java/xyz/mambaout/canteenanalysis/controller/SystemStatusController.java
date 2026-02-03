package xyz.mambaout.canteenanalysis.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import xyz.mambaout.canteenanalysis.entity.vo.SystemStatusVO;
import xyz.mambaout.canteenanalysis.mapper.SystemStatusMapper;

import java.util.List;
import java.util.Map;

/**
 * 系统概览统计接口（学生数、消费总额、贫困生数）。
 */
@RestController
@RequestMapping("/system")
@Slf4j
public class SystemStatusController {
    @Autowired
    private SystemStatusMapper systemStatusMapper;

    @Value("${fastapi.base-url:http://127.0.0.1:8000}")
    private String fastapiBaseUrl;

    /**
     * 返回系统概览统计数据。
     */
    @GetMapping("/status")
    public SystemStatusVO getSystemStatus() {
        SystemStatusVO vo = new SystemStatusVO();
        vo.setTotalStudents(systemStatusMapper.countStudents());
        vo.setTodayConsumption(systemStatusMapper.sumTodayConsumption());
        vo.setMonthlyConsumption(systemStatusMapper.sumMonthlyConsumption());
        vo.setPovertyStudents(fetchPovertyCount());
        return vo;
    }

    /**
     * 通过 FastAPI 聚类接口统计贫困生人数。
     */
    private Long fetchPovertyCount() {
        try {
            RestTemplate restTemplate = new RestTemplate();
            String url = fastapiBaseUrl + "/analysis/cluster";
            Map<?, ?> resp = restTemplate.getForObject(url, Map.class);
            if (resp == null) {
                return 0L;
            }
            Object results = resp.get("results");
            if (results instanceof List) {
                long count = ((List<?>) results).stream().filter(item -> {
                    if (!(item instanceof Map)) return false;
                    Object type = ((Map<?, ?>) item).get("clusterType");
                    return "贫困生".equals(type);
                }).count();
                return count;
            }
        } catch (Exception e) {
            log.warn("fetchPovertyCount failed: {}", e.getMessage());
        }
        return 0L;
    }
}