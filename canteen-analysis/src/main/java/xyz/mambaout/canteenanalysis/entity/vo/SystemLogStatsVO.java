package xyz.mambaout.canteenanalysis.entity.vo;

import lombok.Data;

@Data
public class SystemLogStatsVO {
    private Long totalLogs;
    private Long successLogs;
    private Long failureLogs;
    private Long uniqueUsers;
}