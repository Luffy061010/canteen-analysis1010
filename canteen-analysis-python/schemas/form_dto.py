from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class ConfigMixin:
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }
        allow_population_by_field_name = True
        extra = "ignore"


class BaseBody(ConfigMixin, BaseModel):
    """基础请求参数"""
    college: Optional[str] = Field(None, description="学院")
    major: Optional[str] = Field(None, description="专业")
    grade: Optional[str] = Field(None, description="年级")
    className: Optional[str] = Field(None, description="班级", alias="className")
    studentId: Optional[str] = Field(None, description="学号", alias="studentId")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    timeBegin: Optional[date] = Field(None, description="开始日期", alias="timeBegin")
    timeEnd: Optional[date] = Field(None, description="结束日期", alias="timeEnd")
    timeWindow: Optional[int] = Field(7, description="时间窗口(天)", alias="timeWindow")


# 其他模型保持不变
class ClusterBody(BaseBody):
    # 如果有集群分析的特定参数
    n_clusters: Optional[int] = Field(4, description="聚类数量", alias="n_clusters")
    clusterNums: Optional[int] = Field(None, description="聚类数量(兼容前端字段)", alias="clusterNums")


class CorrelationBody(BaseBody):
    # 如果有相关性分析的特定参数
    method: Optional[str] = Field("pearson", description="相关性计算方法", alias="correlationMethod")
    term: Optional[str] = Field(None, description="学期")


class DriftBody(BaseBody):
    # 漂移分析特定参数（继承 timeWindow 等）
    timeWindow: Optional[int] = Field(7, description="时间窗口(天)", alias="timeWindow")

