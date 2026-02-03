from schemas.form_dto import ClusterBody, DriftBody, CorrelationBody, BaseBody
from utils.get_data_summary import get_data_summary, get_data_summary_gpa
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from scipy import stats
from utils.data_drift import EIkMeans
from datetime import timedelta, date, datetime
from fastapi import HTTPException
import pymysql
from config import mysql
import numpy as np


def normalize_student_id(value):
    if value is None:
        return ""
    sid = str(value).strip()
    # 去前导 0，保持字符串
    sid = sid.lstrip("0") or "0"
    return sid

def analysis_cluster(cluster_body:ClusterBody):
    df = get_data_summary(cluster_body)
    if df.empty:
        return {"centers": [], "data": [], "results": [], "clusterData": [], "distributionData": []}

    # 计算日均消费与日均次数
    amount_cols = ["breakfast_avg_amount", "lunch_avg_amount", "dinner_avg_amount"]
    count_cols = ["breakfast_avg_count", "lunch_avg_count", "dinner_avg_count"]
    df["dailyAvg"] = df[amount_cols].sum(axis=1)
    df["dailyCount"] = df[count_cols].sum(axis=1)

    feature_df = df[["dailyAvg", "dailyCount"]].copy()
    min_max_scaler = MinMaxScaler()
    scalared_df = min_max_scaler.fit_transform(feature_df)

    # 兼容 n_clusters / clusterNums 字段
    n_samples = len(df)
    n_clusters_val = cluster_body.n_clusters if cluster_body.n_clusters is not None else cluster_body.clusterNums
    n_clusters = int(n_clusters_val or 4)
    # 当样本很少（例如只筛选一个学号）时，避免 KMeans 报错
    n_clusters = min(n_clusters, n_samples)
    if n_clusters < 1:
        n_clusters = 1

    if n_samples == 1:
        labels = np.array([0])
        centers = scalared_df
    else:
        kmeans = KMeans(n_clusters=n_clusters, n_init=10)
        labels = kmeans.fit_predict(scalared_df)
        centers = kmeans.cluster_centers_

    centers_inv = min_max_scaler.inverse_transform(centers)
    centers_df = pd.DataFrame(centers_inv, columns=["dailyAvg", "dailyCount"])

    df["label"] = labels

    # 拉取学生姓名/学院映射
    def normalize_student_id(value):
        if value is None:
            return ""
        sid = str(value).strip()
        if sid.isdigit():
            sid = sid.lstrip("0") or "0"
        return sid

    conn = pymysql.connect(**mysql.DBCONFIG)
    cur = conn.cursor()
    # 取出姓名、学院、专业、班级，方便前端展示（可按学号过滤加速）
    if cluster_body.studentId:
        cur.execute(
            "SELECT student_id, name, college, major, class_name FROM basic_data_student WHERE student_id=%s",
            (cluster_body.studentId,)
        )
    else:
        cur.execute("SELECT student_id, name, college, major, class_name FROM basic_data_student")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    name_map = {}
    for r in rows:
        sid_key = normalize_student_id(r[0])
        if not sid_key:
            continue
        name_map[sid_key] = {
            "name": r[1] or "-",
            "college": r[2] or "-",
            "major": r[3] or "-",
            "className": r[4] or "-"
        }

    # 聚类类型命名（按日均消费排序，最低为贫困）
    center_order = centers_df["dailyAvg"].sort_values().index.tolist()
    type_names = ["贫困生", "低消费", "中等消费", "高消费", "高消费2", "高消费3"]
    label_to_type = {}
    for rank, label_idx in enumerate(center_order):
        label_to_type[label_idx] = type_names[min(rank, len(type_names)-1)]

    results = []
    cluster_points = []
    distribution_count = {}

    for sid, row in df.iterrows():
        sid_str = str(sid).strip()
        info = name_map.get(normalize_student_id(sid_str), {})
        name = info.get("name", "-")
        college = info.get("college", "-")
        major = info.get("major", "-")
        class_name = info.get("className", "-")
        daily = float(row["dailyAvg"])
        daily_count = float(row["dailyCount"])
        label = int(row["label"])
        cluster_type = label_to_type.get(label, "普通消费")

        center_vec = centers[label]
        point_vec = scalared_df[df.index.get_loc(sid)]
        dist = float(np.linalg.norm(point_vec - center_vec))
        confidence = max(0.0, min(100.0, (1.0 - dist) * 100.0))
        poverty_index = round(1.0 - daily / (centers_df["dailyAvg"].max() + 1e-6), 4)

        results.append({
            "studentId": sid_str,
            "name": name,
            "college": college,
            "major": major,
            "className": class_name,
            "monthlyAvg": round(daily, 2),
            "dailyAvg": round(daily, 2),
            "dailyCount": round(daily_count, 2),
            "clusterType": cluster_type,
            "povertyIndex": round(poverty_index, 4),
            "confidence": round(confidence, 2)
        })

        cluster_points.append({
            "x": round(daily, 2),
            "y": round(daily_count, 2),
            "label": cluster_type,
            "studentId": sid_str,
            "name": name,
            "major": major,
            "className": class_name
        })

        distribution_count[cluster_type] = distribution_count.get(cluster_type, 0) + 1

    distribution_data = [
        {"name": k, "value": v} for k, v in distribution_count.items()
    ]

    return {
        "centers": centers_df.to_dict(orient="records"),
        "data": feature_df.to_dict(orient="records"),
        "results": results,
        "clusterData": cluster_points,
        "distributionData": distribution_data
    }

def analysis_drift(drift_body:DriftBody):
    # 1-30 日
    # 1-8 (val1) 8-15 (val2) 15-22 (val3) 22-29
    time_begin = drift_body.timeBegin or drift_body.start_date
    time_end = drift_body.timeEnd or drift_body.end_date
    time_window = int(drift_body.timeWindow or 7)

    if not time_begin or not time_end:
        raise HTTPException(status_code=400, detail="缺少时间范围")

    if isinstance(time_begin, datetime):
        time_begin = time_begin.date()
    if isinstance(time_end, datetime):
        time_end = time_end.date()

    time_duration = (time_end - time_begin).days
    if time_duration < time_window * 2:
        raise HTTPException(status_code=400, detail="时间范围需至少覆盖两个时间窗口")

    left_time  = time_begin
    middle_time = time_begin + timedelta(days=time_window)
    right_time = time_begin + timedelta(days=time_window*2)
    # 步长：设为 1 天，生成更密集的采样点
    step_days = 1

    df_left = get_data_summary(BaseBody(
        college=drift_body.college,
        major=drift_body.major,
        grade=drift_body.grade,
        className=drift_body.className,
        timeBegin=left_time,
        timeEnd=middle_time
    ))
    p_values = []
    results = []
    dates = []
    consumption_actual = []
    consumption_trend = []
    consumption_drift_points = []
    # 使用滑动窗口（步长 < 窗口）提高点密度
    idx = 0

    # 一次性加载学生姓名映射，避免循环内重复建连查询
    def load_student_map():
        conn = pymysql.connect(**mysql.DBCONFIG)
        cur = conn.cursor()
        sql = "SELECT student_id, name, college FROM basic_data_student WHERE 1=1"
        params = []
        if drift_body.college:
            sql += " AND college=%s"
            params.append(drift_body.college)
        if drift_body.major:
            sql += " AND major=%s"
            params.append(drift_body.major)
        if drift_body.grade:
            sql += " AND grade=%s"
            params.append(drift_body.grade)
        if drift_body.className:
            sql += " AND class_name=%s"
            params.append(drift_body.className)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {str(r[0]): {"name": r[1], "college": r[2]} for r in rows}

    name_cache = load_student_map()
    while right_time <= time_end:
        df_right = get_data_summary(BaseBody(
            college=drift_body.college,
            major=drift_body.major,
            grade=drift_body.grade,
            className=drift_body.className,
            timeBegin=middle_time,
            timeEnd=right_time
        ))
        data_train = df_left.values
        data_test = df_right.values

        min_max_scalar = MinMaxScaler()
        data_train = min_max_scalar.fit_transform(data_train)
        data_test = min_max_scalar.transform(data_test)

        model = EIkMeans(40)
        model.build_partition(data_train,data_test.shape[0])
        p = model.drift_detection2(data_test,0.05)
        p_values.append(p)
        confidence_from_p = max(0.0, min(100.0, (1.0 - float(p)) * 100.0))

        # 生成消费序列（用于消费模式图表）
        meal_cols = ["breakfast_avg_amount", "lunch_avg_amount", "dinner_avg_amount"]
        if not df_left.empty:
            left_daily = df_left[meal_cols].sum(axis=1).mean()
        else:
            left_daily = 0.0
        if not df_right.empty:
            right_daily = df_right[meal_cols].sum(axis=1).mean()
        else:
            right_daily = 0.0
        consumption_actual.append(round(float(right_daily), 2))
        consumption_trend.append(round(float(left_daily), 2))
        consumption_drift_points.append(round(float(right_daily), 2) if p < 0.05 else None)

        # 生成表格结果：对每个学生计算漂移前后均值
        common_ids = df_left.index.intersection(df_right.index)
        detect_date = right_time

        # 单体漂移：仅针对指定学号
        if drift_body.studentId:
            sid_str = str(drift_body.studentId)
            before_mean = float(df_left.loc[sid_str].mean()) if sid_str in df_left.index else 0.0
            after_mean = float(df_right.loc[sid_str].mean()) if sid_str in df_right.index else 0.0
            change_rate = float(after_mean - before_mean) / abs(before_mean + 1e-9) * 100 if before_mean != 0 else 0.0
            # 置信度：基于统计显著性 (1 - p)
            confidence = confidence_from_p
            info = name_cache.get(sid_str, {})
            results.append({
                "studentId": sid_str,
                "name": info.get("name", "-"),
                "college": drift_body.college or info.get("college", "-"),
                "beforeDrift": round(before_mean, 2),
                "afterDrift": round(after_mean, 2),
                "changeRate": round(change_rate, 2),
                "confidence": round(confidence, 2),
                "detectDate": detect_date.isoformat()
            })
        else:
            if len(common_ids) == 0:
                dates.append(detect_date.isoformat())
                middle_time += timedelta(days=step_days)
                right_time += timedelta(days=step_days)
                left_time += timedelta(days=step_days)
                idx += 1
                df_left = df_right
                continue

            before_mean_series = df_left.loc[common_ids].mean(axis=1)
            after_mean_series = df_right.loc[common_ids].mean(axis=1)

            for sid in common_ids:
                sid_str = str(sid)
                before_mean = float(before_mean_series.get(sid, 0.0))
                after_mean = float(after_mean_series.get(sid, 0.0))
                change_rate = float(after_mean - before_mean) / abs(before_mean + 1e-9) * 100 if before_mean != 0 else 0.0
                # 置信度：基于统计显著性 (1 - p)
                confidence = confidence_from_p
                info = name_cache.get(sid_str, {})
                results.append({
                    "studentId": sid_str,
                    "name": info.get("name", "-"),
                    "college": drift_body.college or info.get("college", "-"),
                    "beforeDrift": round(before_mean, 2),
                    "afterDrift": round(after_mean, 2),
                    "changeRate": round(change_rate, 2),
                    "confidence": round(confidence, 2),
                    "detectDate": detect_date.isoformat()
                })

        dates.append(detect_date.isoformat())
        middle_time += timedelta(days=step_days)
        right_time += timedelta(days=step_days)
        left_time += timedelta(days=step_days)
        idx += 1
        df_left = df_right

    print(p_values)
    return {
        "p_values": p_values,
        "time_window": time_window,
        "time_begin": time_begin.isoformat(),
        "time_end": time_end.isoformat(),
        "results": results,
        "chartData": {
            "dates": dates,
            "values": {
                "actual": consumption_actual,
                "trend": consumption_trend,
                "driftPoints": consumption_drift_points
            }
        }
    }

def analysis_correlation(correlation_body:CorrelationBody):
    term = getattr(correlation_body, "term", None)
    # 时间范围可选；不传则使用全量消费
    time_begin = correlation_body.timeBegin or correlation_body.start_date
    time_end = correlation_body.timeEnd or correlation_body.end_date
    if isinstance(time_begin, datetime):
        time_begin = time_begin.date()
    if isinstance(time_end, datetime):
        time_end = time_end.date()
    # 汇总消费数据（按筛选条件）
    summary_df = get_data_summary(BaseBody(
        college=correlation_body.college,
        major=correlation_body.major,
        grade=correlation_body.grade,
        className=correlation_body.className,
        studentId=correlation_body.studentId,
        timeBegin=time_begin,
        timeEnd=time_end
    ))
    if summary_df.empty:
        return {"scatterData": [], "correlationResults": [], "message": "筛选条件下无消费数据", "meta": {"consumptionCount": 0, "gpaCount": 0, "mergedCount": 0}}

    # 计算日均/月均消费
    meal_cols = ["breakfast_avg_amount", "lunch_avg_amount", "dinner_avg_amount"]
    summary_df["dailyAvg"] = summary_df[meal_cols].sum(axis=1)
    summary_df["monthlyAvg"] = summary_df["dailyAvg"] * 30
    summary_df = summary_df.reset_index().rename(columns={"index": "student_id"})
    summary_df["norm_id"] = summary_df["student_id"].apply(normalize_student_id)

    # 获取 GPA（若未传学期且指定学号，则自动取该学号最新学期）
    conn = pymysql.connect(**mysql.DBCONFIG)
    cur = conn.cursor()
    if not term:
        # 单个学号：取该学号最新学期；否则取全库最新学期，避免前端必须填写
        if correlation_body.studentId:
            cur.execute(
                "SELECT term FROM basic_data_score WHERE student_id = %s ORDER BY term DESC LIMIT 1",
                (correlation_body.studentId,)
            )
        else:
            cur.execute("SELECT term FROM basic_data_score ORDER BY term DESC LIMIT 1")
        row = cur.fetchone()
        term = row[0] if row else None

    # 取每个学生的最新学期 GPA，可选学号/院系/专业/年级/班级过滤
    where_sql = " WHERE 1=1"
    params = []
    if correlation_body.studentId:
        where_sql += " AND s.student_id = %s"
        params.append(correlation_body.studentId)
    if correlation_body.college:
        where_sql += " AND s.college = %s"
        params.append(correlation_body.college)
    if correlation_body.major:
        where_sql += " AND s.major = %s"
        params.append(correlation_body.major)
    if correlation_body.grade:
        where_sql += " AND s.grade = %s"
        params.append(correlation_body.grade)
    if correlation_body.className:
        where_sql += " AND s.class_name = %s"
        params.append(correlation_body.className)

    gpa_sql = f"""
        SELECT bs.student_id, bs.gpa, bs.term
        FROM basic_data_score bs
        JOIN (
            SELECT student_id, MAX(term) AS term FROM basic_data_score GROUP BY student_id
        ) t ON t.student_id = bs.student_id AND t.term = bs.term
        JOIN basic_data_student s ON s.student_id = bs.student_id
        {where_sql}
    """
    cur.execute(gpa_sql, params)
    rows = cur.fetchall()
    term_used = "per-student-latest"
    fallback_msg = None
    # rows 可能包含 term 列，先裁剪成 (student_id, gpa)
    rows_trimmed = [(r[0], r[1]) for r in rows]
    gpa_df = pd.DataFrame(data=rows_trimmed, columns=["student_id", "gpa"])
    gpa_df["norm_id"] = gpa_df["student_id"].apply(normalize_student_id)
    cur.close()
    conn.close()
    if gpa_df.empty:
        return {"scatterData": [], "correlationResults": [], "message": "指定条件暂无成绩数据", "meta": {"consumptionCount": int(len(summary_df)), "gpaCount": 0, "mergedCount": 0, "termUsed": term_used}}
    gpa_df["gpa"] = gpa_df["gpa"].astype(float)

    # 合并
    merged = summary_df.merge(gpa_df, on="norm_id", how="inner", suffixes=("_cons", "_gpa"))
    if merged.empty:
        return {"scatterData": [], "correlationResults": [], "message": "消费数据与成绩数据无交集", "meta": {"consumptionCount": int(len(summary_df)), "gpaCount": int(len(gpa_df)), "mergedCount": 0, "termUsed": term_used}}

    # 生成散点图数据：x 为日均消费，y 为 GPA
    scatter_data = [
        {
            "x": float(row["dailyAvg"]),
            "y": float(row["gpa"]),
            "studentId": str(row.get("student_id_cons") or row.get("student_id"))
        }
        for _, row in merged.iterrows()
    ]

    # 相关性分析
    method = (getattr(correlation_body, "method", "pearson") or "pearson").lower()
    factor_map = {
        "breakfast_avg_amount": "早餐均额",
        "lunch_avg_amount": "午餐均额",
        "dinner_avg_amount": "晚餐均额",
        "dailyAvg": "日均消费",
        "monthlyAvg": "月均消费"
    }
    results = []
    for col, label in factor_map.items():
        series = merged[col]
        if series.nunique() < 2:
            corr, p = 0.0, 1.0
        else:
            if method == "spearman":
                corr, p = stats.spearmanr(series, merged["gpa"])
            elif method == "pearson":
                corr, p = stats.pearsonr(series, merged["gpa"])
            else:
                raise HTTPException(status_code=400, detail="不支持的相关性方法")
        significance = "显著" if p < 0.05 else "不显著"
        if corr >= 0.3:
            interp = "正相关"
        elif corr <= -0.3:
            interp = "负相关"
        else:
            interp = "相关性弱"
        results.append({
            "factor": label,
            "correlation": float(corr),
            "pValue": float(p),
            "significance": significance,
            "interpretation": interp
        })

    student_profile = None
    if correlation_body.studentId:
        sid = normalize_student_id(correlation_body.studentId)
        try:
            profile_row = merged[merged["norm_id"] == sid]
            profile_cons = profile_row.iloc[0] if len(profile_row) > 0 else None
        except Exception:
            profile_cons = None

        if profile_cons is None:
            try:
                summary_row = summary_df[summary_df["norm_id"] == sid]
                profile_cons = summary_row.iloc[0] if len(summary_row) > 0 else None
            except Exception:
                profile_cons = None

        conn = pymysql.connect(**mysql.DBCONFIG)
        cur = conn.cursor()
        cur.execute(
            "SELECT student_id, name, college, major, class_name, grade FROM basic_data_student WHERE student_id=%s",
            (correlation_body.studentId,)
        )
        srow = cur.fetchone()
        cur.close()
        conn.close()

        # 基于群体分布的消费群体划分
        try:
            q20 = float(merged["dailyAvg"].quantile(0.2))
            q50 = float(merged["dailyAvg"].quantile(0.5))
            q80 = float(merged["dailyAvg"].quantile(0.8))
        except Exception:
            q20, q50, q80 = 0.0, 0.0, 0.0

        def classify_group(daily_avg: float) -> str:
            if daily_avg <= q20:
                return "贫困生"
            if daily_avg <= q50:
                return "低消费"
            if daily_avg <= q80:
                return "中等消费"
            return "高消费"

        daily_avg_val = float(profile_cons["dailyAvg"]) if profile_cons is not None else 0.0
        gpa_val = float(profile_cons["gpa"]) if (profile_cons is not None and "gpa" in profile_cons) else 0.0

        student_profile = {
            "studentId": str(correlation_body.studentId),
            "name": srow[1] if srow else "-",
            "college": srow[2] if srow else "-",
            "major": srow[3] if srow else "-",
            "className": srow[4] if srow else "-",
            "grade": srow[5] if srow else "-",
            "gpa": gpa_val,
            "dailyAvg": daily_avg_val,
            "monthlyAvg": float(profile_cons["monthlyAvg"]) if profile_cons is not None else 0.0,
            "consumptionGroup": classify_group(daily_avg_val)
        }

    return {
        "scatterData": scatter_data,
        "correlationResults": results,
        "studentProfile": student_profile,
        "meta": {
            "consumptionCount": int(len(summary_df)),
            "gpaCount": int(len(gpa_df)),
            "mergedCount": int(len(merged)),
            "avgDaily": float(merged["dailyAvg"].mean()),
            "avgGpa": float(merged["gpa"].mean()),
            "termUsed": term_used,
            "method": method,
            "fallback": fallback_msg if fallback_msg else None
        }
    }
