package xyz.mambaout.canteenanalysis.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.SystemLog;
import xyz.mambaout.canteenanalysis.entity.query.LogQuery;
import xyz.mambaout.canteenanalysis.mapper.SystemLogMapper;
import xyz.mambaout.canteenanalysis.service.ISystemLogService;
import xyz.mambaout.canteenanalysis.entity.vo.SystemLogStatsVO;

import java.util.List;

/**
 * 系统日志服务实现：查询、导出、删除与统计。
 */
@Service
public class SystemLogServiceImpl implements ISystemLogService {
    @Autowired
    private SystemLogMapper systemLogMapper;

    /**
     * 分页查询日志。
     */
    @Override
    public PageResult<SystemLog> queryLogs(LogQuery query) {
        Integer pageNum = query.getPage() == null || query.getPage() < 1 ? 1 : query.getPage();
        Integer pageSize = query.getPageSize() == null || query.getPageSize() < 1 ? 10 : query.getPageSize();

        PageHelper.startPage(pageNum, pageSize);
        List<SystemLog> list = systemLogMapper.queryLogs(query);
        PageInfo<SystemLog> pageInfo = new PageInfo<>(list);

        PageResult<SystemLog> result = new PageResult<>();
        result.setCode(0);
        result.setMsg("success");
        result.setTotal(pageInfo.getTotal());
        result.setPage(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setRecords(pageInfo.getList());
        return result;
    }

    /**
     * 导出日志（不分页）。
     */
    @Override
    public List<SystemLog> exportLogs(LogQuery query) {
        return systemLogMapper.queryLogs(query);
    }

    /**
     * 批量删除日志。
     */
    @Override
    public boolean deleteLogs(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return false;
        }
        return systemLogMapper.deleteByIds(ids) > 0;
    }

    /**
     * 统计日志分布。
     */
    @Override
    public SystemLogStatsVO stats(LogQuery query) {
        return systemLogMapper.stats(query);
    }
}