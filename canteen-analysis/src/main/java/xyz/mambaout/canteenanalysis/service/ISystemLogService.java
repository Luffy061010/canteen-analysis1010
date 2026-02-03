package xyz.mambaout.canteenanalysis.service;

import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.SystemLog;
import xyz.mambaout.canteenanalysis.entity.query.LogQuery;
import xyz.mambaout.canteenanalysis.entity.vo.SystemLogStatsVO;

import java.util.List;

/**
 * 系统日志服务接口。
 */
public interface ISystemLogService {
    /**
     * 分页查询日志。
     */
    PageResult<SystemLog> queryLogs(LogQuery query);

    /**
     * 导出日志列表。
     */
    List<SystemLog> exportLogs(LogQuery query);

    /**
     * 批量删除日志。
     */
    boolean deleteLogs(List<Long> ids);

    /**
     * 日志统计。
     */
    SystemLogStatsVO stats(LogQuery query);
}