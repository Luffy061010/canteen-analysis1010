package xyz.mambaout.canteenanalysis.entity.dto;

import lombok.Data;

import java.util.List;

@Data
public class LogDeleteRequest {
    private List<Long> logIds;
}