# models.py
from pydantic import BaseModel
from typing import Optional


class BaseBody(BaseModel):
    college: Optional[str] = None
    className: Optional[str] = None  # 添加缺失的字段
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # 添加其他可能需要的字段
    grade: Optional[str] = None
    major: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True