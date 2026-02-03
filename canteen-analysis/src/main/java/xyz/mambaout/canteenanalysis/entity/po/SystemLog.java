package xyz.mambaout.canteenanalysis.entity.po;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class SystemLog {
    private Long id;
    private LocalDateTime operationTime;
    private String operator;
    private String operationType;
    private String module;
    private String operationDetail;
    private String ipAddress;
    private String result;
    private Integer executionTime;
    private String requestParams;
    private String responseResult;
}