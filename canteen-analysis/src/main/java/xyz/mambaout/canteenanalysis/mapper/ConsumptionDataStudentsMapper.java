package xyz.mambaout.canteenanalysis.mapper;

import org.apache.ibatis.annotations.MapKey;
import org.apache.ibatis.annotations.Mapper;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudentsConsumption;
import xyz.mambaout.canteenanalysis.entity.query.TimeQuery;
import xyz.mambaout.canteenanalysis.entity.vo.SimpleConsumptionStatVO;

import java.util.List;
import java.util.Map;

@Mapper
public interface ConsumptionDataStudentsMapper {
    List<BasicDataStudentsConsumption> queryStudentComsumption(TimeQuery timeQuery);

    SimpleConsumptionStatVO simpleConsumptionStat(TimeQuery timeQuery);

    @MapKey("")
    List<Map<String, Object>> topWindowStat(TimeQuery timeQuery);

    Map<String, Object> consumptionCompareStat(TimeQuery timeQuery);
}
