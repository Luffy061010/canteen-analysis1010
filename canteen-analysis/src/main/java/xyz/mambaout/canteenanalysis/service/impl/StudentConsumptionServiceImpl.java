package xyz.mambaout.canteenanalysis.service.impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xyz.mambaout.canteenanalysis.entity.page.PageResult;
import xyz.mambaout.canteenanalysis.entity.po.BasicDataStudentsConsumption;
import xyz.mambaout.canteenanalysis.entity.query.TimeQuery;
import xyz.mambaout.canteenanalysis.entity.vo.ConsumptionCompareVO;
import xyz.mambaout.canteenanalysis.entity.vo.SimpleConsumptionStatVO;
import xyz.mambaout.canteenanalysis.entity.vo.TopWindowStatVO;
import xyz.mambaout.canteenanalysis.mapper.ConsumptionDataStudentsMapper;
import xyz.mambaout.canteenanalysis.service.IStudentConsumptionService;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * 学生消费服务实现：消费明细、统计汇总、窗口分布与对比。
 */
@Service
@Slf4j
public class StudentConsumptionServiceImpl implements IStudentConsumptionService {
    @Autowired
    private ConsumptionDataStudentsMapper studentsMapper;
    /**
     * 分页查询消费明细。
     */
    @Override
    public PageResult<BasicDataStudentsConsumption> queryStudentComsumption(TimeQuery timeQuery) {
        int pageNum = Optional.ofNullable(timeQuery.getPage()).orElse(1);
        int pageSize = Optional.ofNullable(timeQuery.getPageSize()).orElse(20);
        PageHelper.startPage(pageNum, pageSize);
        Page<BasicDataStudentsConsumption> page =(Page<BasicDataStudentsConsumption>) studentsMapper.queryStudentComsumption(timeQuery);
        PageResult<BasicDataStudentsConsumption> pageResult = new PageResult<>();
        pageResult.setCode(0);
        pageResult.setMsg("success");
        pageResult.setTotal(page.getTotal());
        pageResult.setPage(page.getPageNum());
        pageResult.setPageSize(page.getPageSize());
        pageResult.setRecords(page.getResult());
        return pageResult;
    }

    /**
     * 消费统计汇总。
     */
    @Override
    public SimpleConsumptionStatVO simpleConsumptionStat(TimeQuery timeQuery) {
        return studentsMapper.simpleConsumptionStat(timeQuery);
    }

    /**
     * 窗口消费 Top 分布统计。
     */
    @Override
    public TopWindowStatVO topWindowStat(TimeQuery timeQuery) {
        List<Map<String,Object>> list = studentsMapper.topWindowStat(timeQuery);
        log.info("topWindowStat: {}", list);
        TopWindowStatVO topWindowStatVO = new TopWindowStatVO();
        double totalAmount = list.stream()
            .map(map -> (BigDecimal) map.get("windowAmount"))
            .filter(Objects::nonNull)
            .mapToDouble(BigDecimal::doubleValue)
            .sum();
        List<String> windowNames = list.stream().map(map -> map.get("windowId") + "号窗口").toList();
        List<Double> windowAmounts = list.stream().map(map -> ((BigDecimal) map.get("windowAmount")).doubleValue()).toList();
        List<Double> windowPercent = windowAmounts.stream().map(amount -> totalAmount == 0 ? 0 : amount / totalAmount).toList();

        topWindowStatVO.setWindowNames(windowNames);
        topWindowStatVO.setWindowAmounts(windowAmounts);
        topWindowStatVO.setWindowPercent(windowPercent);
        return topWindowStatVO;
    }

    /**
     * 消费对比统计。
     */
    @Override
    public ConsumptionCompareVO consumptionCompareStat(TimeQuery timeQuery) {
        Map<String,Object> queryMap = studentsMapper.consumptionCompareStat(timeQuery);
        Map<String,Object> totalMap = studentsMapper.consumptionCompareStat(new TimeQuery(timeQuery.timeBegin,timeQuery.timeEnd));
        log.info("queryMap:{}",queryMap);
        log.info("totalMap:{}",totalMap);
        if(queryMap.get("totalAmount") == null || totalMap.get("totalAmount") == null) {
            return null;
        }
        Double totalAmount = ((BigDecimal) totalMap.get("totalAmount")).doubleValue();
        Integer totalRecords = ((Long) totalMap.get("totalRecords")).intValue();
        Integer totalStudents = ((Long) totalMap.get("totalStudents")).intValue();

        Double apartAmount = ((BigDecimal) queryMap.get("totalAmount")).doubleValue();
        Integer apartRecords = ((Long) queryMap.get("totalRecords")).intValue();
        Integer apartStudents = ((Long) queryMap.get("totalStudents")).intValue();

        return ConsumptionCompareVO
                .builder()
                .selectedAverageAmount(apartAmount / apartStudents)
                .selectedAverageTimes(apartRecords / apartStudents)
                .totalAverageAmount(totalAmount / totalStudents)
                .totalAverageTimes(totalRecords / totalStudents)
                .build();
    }

    /**
     * 导出消费明细（不分页）。
     */
    @Override
    public List<BasicDataStudentsConsumption> exportStudentConsumption(TimeQuery timeQuery) {
        return studentsMapper.queryStudentComsumption(timeQuery);
    }
}
