package xyz.mambaout.canteenanalysis.entity.page;

import lombok.Data;

@Data
public class PageQuery {
    public Integer page = 1;
    public Integer pageSize = 20;
}
