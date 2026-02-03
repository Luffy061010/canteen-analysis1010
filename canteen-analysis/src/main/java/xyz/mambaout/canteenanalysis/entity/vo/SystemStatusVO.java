package xyz.mambaout.canteenanalysis.entity.vo;

import lombok.Data;

@Data
public class SystemStatusVO {
    private Long totalStudents;
    private Double todayConsumption;
    private Double monthlyConsumption;
    private Long povertyStudents;
}