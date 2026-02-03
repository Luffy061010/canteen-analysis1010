package xyz.mambaout.canteenanalysis.service;

import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudentsConsumption;
import xyz.mambaout.canteenanalysis.entity.query.TimeQuery;
import xyz.mambaout.canteenanalysis.entity.vo.ConsumptionCompareVO;
import xyz.mambaout.canteenanalysis.entity.vo.SimpleConsumptionStatVO;
import xyz.mambaout.canteenanalysis.entity.vo.TopWindowStatVO;

/**
 * 学生消费服务接口。
 */
public interface IStudentConsumptionService {

    /**
     * 查询消费明细（分页）。
     */
    PageResult<BasicDataStudentsConsumption> queryStudentComsumption(TimeQuery basicQuery);

    /**
     * 消费统计汇总。
     */
    SimpleConsumptionStatVO simpleConsumptionStat(TimeQuery timeQuery);

    /**
     * 窗口消费 Top 分布。
     */
    TopWindowStatVO topWindowStat(TimeQuery timeQuery);

    /**
     * 消费对比统计。
     */
    ConsumptionCompareVO consumptionCompareStat(TimeQuery timeQuery);

    /**
     * 导出消费明细（不分页）。
     */
    java.util.List<BasicDataStudentsConsumption> exportStudentConsumption(TimeQuery timeQuery);
}
