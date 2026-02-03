package xyz.mambaout.canteenanalysis.entity.po;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class BasicDataStudentsConsumption {
    public String id;
    public String studentId;
    public LocalDateTime consumptionTime;
    public Integer windowId;
    public Double amount;
    public String mealType;

    // Enriched fields from student table for UI display
    public String name;
    public String college;
    public String major;
    public String className;
    public String grade;
}
