package xyz.mambaout.canteenanalysis.entity.query;

import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDate;

@Data
@EqualsAndHashCode(callSuper = true)
public class LogQuery extends xyz.mambaout.canteenanalysis.entity.page.PageQuery {
    private String operationType;
    private String operator;
    private String module;
    private String result;
    private String ipAddress;
    private LocalDate timeBegin;
    private LocalDate timeEnd;
}