package xyz.mambaout.canteenanalysis.entity.vo;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class SimpleConsumptionStatVO {
    public Integer totalAmount;
    public Integer totalRecords;
    public Integer averageConsumption;
    public Integer totalStudents;
}
