"""
数据汇总工具：从原始消费记录生成按学生/时间维度的统计特征。
"""
from schemas.form_dto import BaseBody,CorrelationBody
import pymysql
from config import mysql
import pandas as pd
import numpy as np
from utils import redis_utils as r

def get_data_summary(base_body:BaseBody) -> pd.DataFrame:
    """查询消费明细并聚合为日均消费/次数特征。"""

    connection = pymysql.connect(**mysql.DBCONFIG)
    cursor = connection.cursor()
    sql = """
    SELECT
        s.student_id,
        SUM(CASE WHEN c.meal_type = '早' THEN 1 ELSE 0 END) AS breakfast_count,
        SUM(CASE WHEN c.meal_type = '早' THEN c.amount ELSE 0 END) AS breakfast_amount,
        SUM(CASE WHEN c.meal_type = '中' THEN 1 ELSE 0 END) AS lunch_count,
        SUM(CASE WHEN c.meal_type = '中' THEN c.amount ELSE 0 END) AS lunch_amount,
        SUM(CASE WHEN c.meal_type = '晚' THEN 1 ELSE 0 END) AS dinner_count,
        SUM(CASE WHEN c.meal_type = '晚' THEN c.amount ELSE 0 END) AS dinner_amount
    FROM consumption_data_students_consumption c
    JOIN basic_data_student s ON s.student_id = c.student_id
    WHERE 1=1
    """
    params = []
    if base_body.college:
        sql += " AND s.college = %s"
        params.append(base_body.college)
    if base_body.major:
        sql += " AND s.major = %s"
        params.append(base_body.major)
    if base_body.grade:
        sql += " AND s.grade = %s"
        params.append(base_body.grade)
    if base_body.className:
        sql += " AND s.class_name = %s"
        params.append(base_body.className)
    if base_body.studentId:
        sql += " AND s.student_id = %s"
        params.append(base_body.studentId)
    if base_body.timeBegin and base_body.timeEnd:
        sql += " AND c.consumption_time BETWEEN %s AND %s"
        params.append(base_body.timeBegin)
        params.append(base_body.timeEnd)
    sql += " GROUP BY s.student_id"
    cursor.execute(sql, params)
    res = cursor.fetchall()
    cursor.close()
    connection.close()

    cols = [
        "student_id",
        "breakfast_count",
        "breakfast_amount",
        "lunch_count",
        "lunch_amount",
        "dinner_count",
        "dinner_amount",
    ]
    df = pd.DataFrame(data=res, columns=cols)
    if df.empty:
        return pd.DataFrame(columns=[
            "breakfast_avg_count", "breakfast_avg_amount",
            "lunch_avg_count", "lunch_avg_amount",
            "dinner_avg_count", "dinner_avg_amount"
        ])

    df.set_index("student_id", inplace=True)

    duration = 1
    if base_body.timeEnd and base_body.timeBegin:
        try:
            duration = (base_body.timeEnd - base_body.timeBegin).days
        except Exception:
            duration = 1
    if duration <= 0:
        duration = 1

    res_df = pd.DataFrame(index=df.index, columns=[
        "breakfast_avg_count", "breakfast_avg_amount",
        "lunch_avg_count", "lunch_avg_amount",
        "dinner_avg_count", "dinner_avg_amount"
    ], dtype=float)

    res_df["breakfast_avg_count"] = df["breakfast_count"] / duration
    res_df["breakfast_avg_amount"] = df["breakfast_amount"] / df["breakfast_count"].replace(0, np.nan)
    res_df["lunch_avg_count"] = df["lunch_count"] / duration
    res_df["lunch_avg_amount"] = df["lunch_amount"] / df["lunch_count"].replace(0, np.nan)
    res_df["dinner_avg_count"] = df["dinner_count"] / duration
    res_df["dinner_avg_amount"] = df["dinner_amount"] / df["dinner_count"].replace(0, np.nan)

    res_df.fillna(0, inplace=True)
    res_df = res_df.astype(float).round(2)
    return res_df

def get_data_summary_gpa(correlation_body:CorrelationBody) -> list[pd.DataFrame]:
    """按 GPA 分位区间获取消费特征，用于成绩相关性分析。"""
    connection = pymysql.connect(**mysql.DBCONFIG)
    cursor = connection.cursor()
    sql = "SELECT student_id,gpa FROM basic_data_score WHERE term = %s"
    cursor.execute(sql,correlation_body.term)
    res = cursor.fetchall()
    df = pd.DataFrame(data = res,columns=["student_id","gpa"])
    df["gpa"] = df["gpa"].astype(float)
    lower = df["gpa"].quantile(0.25)
    upper = df["gpa"].quantile(0.75)
    innerSQL = "1=1"
    params = []
    params.append(correlation_body.timeBegin)
    params.append(correlation_body.timeEnd)
    params.append(0)
    params.append(lower)
    params.append(correlation_body.term)

    if correlation_body.college:
        innerSQL += " AND s.college = %s"
        params.append(correlation_body.college)
    if correlation_body.major:
        innerSQL += " AND s.major = %s"
        params.append(correlation_body.major)
    if correlation_body.grade:
        innerSQL += " AND s.grade = %s"
        params.append(correlation_body.grade)
    if correlation_body.className:
        innerSQL += " AND s.class_name = %s"
        params.append(correlation_body.className)


    sql = f"""
    SELECT c.* FROM consumption_data_students_consumption c
    WHERE c.consumption_time BETWEEN %s AND %s AND student_id IN(
        SELECT student_id FROM basic_data_score WHERE gpa BETWEEN %s AND %s AND term = %s AND basic_data_score.student_id in (
            SELECT student_id FROM basic_data_student s WHERE {innerSQL}
        )
    )
    """
    cursor.execute(sql, params)
    res1 = cursor.fetchall()
    df1 = pd.DataFrame(data = res1,columns=["id","student_id","consumption_time","window_id","amount", "meal_type"])
    df1.set_index("id",inplace=True)
    df1 = summary(df1, correlation_body)


    params[2] = lower
    params[3] = upper
    cursor.execute(sql, params)
    res2 = cursor.fetchall()
    df2 = pd.DataFrame(data = res2,columns=["id","student_id","consumption_time","window_id","amount", "meal_type"])
    df2.set_index("id",inplace=True)
    df2 = summary(df2, correlation_body)

    params[2] = upper
    params[3] = 100
    cursor.execute(sql, params)
    res3 = cursor.fetchall()
    df3 = pd.DataFrame(data = res3,columns=["id","student_id","consumption_time","window_id","amount", "meal_type"])
    df3.set_index("id",inplace=True)
    df3 = summary(df3, correlation_body)

    return [df,df1, df2, df3]

def summary(df:pd.DataFrame,base_body:BaseBody):
    """将原始消费记录聚合为早餐/午餐/晚餐的日均次数与金额。"""
    # 无数据时直接返回空表，避免后续列访问报错
    empty_cols = [
        "breakfast_avg_count", "breakfast_avg_amount",
        "lunch_avg_count", "lunch_avg_amount",
        "dinner_avg_count", "dinner_avg_amount"
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=empty_cols)

    middle_res_dict = {}
    for index, row in df.iterrows():
        student_id = row.get("student_id")
        if student_id not in middle_res_dict:
            middle_res_dict[student_id] = {
                "breakfast_count": 0,
                "breakfast_amount": 0,
                "lunch_count": 0,
                "lunch_amount": 0,
                "dinner_count": 0,
                "dinner_amount": 0,
            }
        if row.get("meal_type") == "早":
            middle_res_dict[student_id]["breakfast_count"] += 1
            middle_res_dict[student_id]["breakfast_amount"] += row.get("amount")
        elif row.get("meal_type") == "中":
            middle_res_dict[student_id]["lunch_count"] += 1
            middle_res_dict[student_id]["lunch_amount"] += row.get("amount")
        elif row.get("meal_type") == "晚":
            middle_res_dict[student_id]["dinner_count"] += 1
            middle_res_dict[student_id]["dinner_amount"] += row.get("amount")
    middle_df = pd.DataFrame(data=middle_res_dict).T
    # 早中晚平均金额等于 对应总金额除以总次数  日均次数 次均金额 等于 全部次数除以日期 /全部金额 除以 次数
    duration = (base_body.timeEnd - base_body.timeBegin).days if base_body.timeEnd and base_body.timeBegin else 0
    if duration <= 0:
        duration = 1
    res = pd.DataFrame(index=middle_df.index, columns=empty_cols, dtype=float)
    res["breakfast_avg_count"] = middle_df["breakfast_count"] / duration
    res["breakfast_avg_amount"] = middle_df["breakfast_amount"] / middle_df["breakfast_count"].where(
        middle_df["breakfast_count"] != 0, np.nan)
    res["lunch_avg_count"] = middle_df["lunch_count"] / duration
    res["lunch_avg_amount"] = middle_df["lunch_amount"] / middle_df["lunch_count"].where(middle_df["lunch_count"] != 0,
                                                                                         np.nan)
    res["dinner_avg_count"] = middle_df["dinner_count"] / duration
    res["dinner_avg_amount"] = middle_df["dinner_amount"] / middle_df["dinner_count"].where(
        middle_df["dinner_count"] != 0, np.nan)
    res.fillna(0, inplace=True)
    res = res.astype(float).round(2)
    return res
