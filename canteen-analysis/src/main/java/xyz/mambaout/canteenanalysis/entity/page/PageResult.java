package xyz.mambaout.canteenanalysis.entity.page;

import lombok.Data;

import java.util.List;

@Data
public class PageResult<T> {
    private int code;
    private String msg;
    private Long total;
    private Integer page;
    private Integer pageSize;
    private List<T> records;
}
