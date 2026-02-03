package xyz.mambaout.canteenanalysis.entity.po;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class BasicDataStudent {

    private String studentId;
    private String grade;
    private String college;
    private String major;
    private String name;
    private String className;
    private String gender;
    private String phoneNumber;

}
