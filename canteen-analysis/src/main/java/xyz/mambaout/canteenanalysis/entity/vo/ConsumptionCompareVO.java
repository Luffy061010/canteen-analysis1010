package xyz.mambaout.canteenanalysis.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ConsumptionCompareVO {
    public Double selectedAverageAmount;
    public Double totalAverageAmount;
    public Integer selectedAverageTimes;
    public Integer totalAverageTimes; // 人均
}
