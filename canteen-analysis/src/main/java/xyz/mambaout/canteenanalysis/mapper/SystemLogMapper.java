package xyz.mambaout.canteenanalysis.mapper;

import org.apache.ibatis.annotations.Mapper;
import xyz.mambaout.canteenanalysis.entity.po.SystemLog;
import xyz.mambaout.canteenanalysis.entity.query.LogQuery;
import xyz.mambaout.canteenanalysis.entity.vo.SystemLogStatsVO;

import java.util.List;

@Mapper
public interface SystemLogMapper {
    List<SystemLog> queryLogs(LogQuery query);

    long countLogs(LogQuery query);

    int deleteByIds(List<Long> ids);

    SystemLogStatsVO stats(LogQuery query);
}