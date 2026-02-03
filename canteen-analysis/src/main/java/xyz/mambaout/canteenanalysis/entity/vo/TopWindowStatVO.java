package xyz.mambaout.canteenanalysis.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class TopWindowStatVO {
    List<String> windowNames;
    List<Double> windowAmounts;
    List<Double> windowPercent;
}
