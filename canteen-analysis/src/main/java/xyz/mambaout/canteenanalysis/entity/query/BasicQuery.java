package xyz.mambaout.canteenanalysis.entity.query;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.EqualsAndHashCode;
import xyz.mambaout.canteenanalysis.entity.page.PageQuery;

@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@NoArgsConstructor
public class BasicQuery extends PageQuery {
    public String grade;
    public String college;
    public String major;
    public String className;
    public String studentId;
    public String name;
    public String gender;
    public String phone;
}
