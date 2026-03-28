"""
分析服务：聚类、漂移检测、相关性等核心算法入口。
"""
from schemas.form_dto import ClusterBody, DriftBody, CorrelationBody, BaseBody
from utils.get_data_summary import get_data_summary, get_data_summary_gpa
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from scipy import stats
from utils.data_drift import EIkMeans
from utils.llm_explainer import build_student_portrait_explanation, build_cluster_summary_explanation
from datetime import timedelta, date, datetime
from fastapi import HTTPException
import pymysql
from config import mysql
import numpy as np

_STUDENT_GENDER_COL_CACHE = None


def _safe_number(value, default=0.0):
    try:
        n = float(value)
        if np.isnan(n):
            return float(default)
        return n
    except Exception:
        return float(default)


def _build_filter_sql(base_body):
    where_parts = ["1=1"]
    params = []

    if base_body.college:
        where_parts.append("s.college = %s")
        params.append(base_body.college)
    if base_body.major:
        where_parts.append("s.major = %s")
        params.append(base_body.major)
    if base_body.grade:
        where_parts.append("s.grade = %s")
        params.append(base_body.grade)
    if base_body.className:
        where_parts.append("s.class_name = %s")
        params.append(base_body.className)
    if base_body.studentId:
        where_parts.append("s.student_id = %s")
        params.append(base_body.studentId)

    return " AND ".join(where_parts), params


def _resolve_student_gender_column(cur):
    global _STUDENT_GENDER_COL_CACHE
    if _STUDENT_GENDER_COL_CACHE is not None:
        return _STUDENT_GENDER_COL_CACHE or None

    cur.execute("SHOW COLUMNS FROM basic_data_student")
    student_columns = {row[0] for row in cur.fetchall()}
    if "gender" in student_columns:
        _STUDENT_GENDER_COL_CACHE = "gender"
    elif "sex" in student_columns:
        _STUDENT_GENDER_COL_CACHE = "sex"
    else:
        _STUDENT_GENDER_COL_CACHE = ""

    return _STUDENT_GENDER_COL_CACHE or None


def get_dashboard_overview(base_body: BaseBody):
    """首页轻量聚合数据：避免前端拼装大明细列表。"""
    where_sql, filter_params = _build_filter_sql(base_body)

    conn = pymysql.connect(**mysql.DBCONFIG)
    cur = conn.cursor()

    # 默认时间范围不使用“今天”，而是锚定到库内最新消费日期，避免历史数据集首页全 0。
    max_date_sql = f"""
        SELECT MAX(c.consumption_time)
        FROM consumption_data_students_consumption c
        INNER JOIN basic_data_student s ON s.student_id = c.student_id
        WHERE {where_sql}
    """
    cur.execute(max_date_sql, filter_params)
    global_latest_ts = cur.fetchone()[0]

    time_begin = base_body.timeBegin or base_body.start_date
    time_end = base_body.timeEnd or base_body.end_date
    if not time_end:
        if global_latest_ts:
            time_end = global_latest_ts.date()
        else:
            time_end = date.today()
    if not time_begin:
        time_begin = time_end - timedelta(days=29)
    if time_begin > time_end:
        time_begin, time_end = time_end, time_begin

    time_end_next = time_end + timedelta(days=1)

    # 1) 总学生数
    count_sql = f"SELECT COUNT(1) FROM basic_data_student s WHERE {where_sql}"
    cur.execute(count_sql, filter_params)
    total_students = int(cur.fetchone()[0] or 0)

    # 2) 最近时间点（限定筛选范围与时间区间）
    latest_sql = f"""
        SELECT MAX(c.consumption_time)
        FROM consumption_data_students_consumption c
        INNER JOIN basic_data_student s ON s.student_id = c.student_id
        WHERE {where_sql}
          AND c.consumption_time >= %s
          AND c.consumption_time < %s
    """
    latest_params = list(filter_params) + [time_begin, time_end_next]
    cur.execute(latest_sql, latest_params)
    latest_ts = cur.fetchone()[0]

    latest_24h_amount = 0.0
    latest_24h_records = 0
    hourly_amount = [0.0] * 24
    latest_day = None

    if latest_ts:
        latest_day = latest_ts.date().isoformat()
        range_24h_begin = latest_ts - timedelta(hours=24)

        # 3) 最近24小时统计
        stat_sql = f"""
            SELECT IFNULL(SUM(c.amount), 0), COUNT(1)
            FROM consumption_data_students_consumption c
            INNER JOIN basic_data_student s ON s.student_id = c.student_id
            WHERE {where_sql}
              AND c.consumption_time >= %s
              AND c.consumption_time <= %s
        """
        stat_params = list(filter_params) + [range_24h_begin, latest_ts]
        cur.execute(stat_sql, stat_params)
        stat_row = cur.fetchone() or (0, 0)
        latest_24h_amount = round(_safe_number(stat_row[0], 0.0), 2)
        latest_24h_records = int(stat_row[1] or 0)

        # 4) 最近一天小时分布
        day_begin = datetime.combine(latest_ts.date(), datetime.min.time())
        day_end = day_begin + timedelta(days=1)
        hour_sql = f"""
            SELECT HOUR(c.consumption_time) AS hour_num, IFNULL(SUM(c.amount), 0) AS hour_amount
            FROM consumption_data_students_consumption c
            INNER JOIN basic_data_student s ON s.student_id = c.student_id
            WHERE {where_sql}
              AND c.consumption_time >= %s
              AND c.consumption_time < %s
            GROUP BY HOUR(c.consumption_time)
        """
        hour_params = list(filter_params) + [day_begin, day_end]
        cur.execute(hour_sql, hour_params)
        for hour_num, hour_amount in cur.fetchall():
            idx = int(hour_num or 0)
            if 0 <= idx < 24:
                hourly_amount[idx] = round(_safe_number(hour_amount, 0.0), 2)

    # 5) 漂移回退分数（基于日总额CV）
    daily_sql = f"""
        SELECT DATE(c.consumption_time) AS d, IFNULL(SUM(c.amount), 0) AS day_amount
        FROM consumption_data_students_consumption c
        INNER JOIN basic_data_student s ON s.student_id = c.student_id
        WHERE {where_sql}
          AND c.consumption_time >= %s
          AND c.consumption_time < %s
        GROUP BY DATE(c.consumption_time)
        ORDER BY DATE(c.consumption_time)
    """
    daily_params = list(filter_params) + [time_begin, time_end_next]
    cur.execute(daily_sql, daily_params)
    daily_series = [float(row[1] or 0.0) for row in cur.fetchall()]
    drift_basis = len(daily_series) >= 3
    if drift_basis:
        mean_val = float(np.mean(daily_series))
        std_val = float(np.std(daily_series))
        cv = (std_val / mean_val) if mean_val > 0 else 0.0
        drift_score = max(0.0, min(100.0, cv * 100.0))
        drift_note = f"回退估算: {len(daily_series)} 天"
    else:
        drift_score = 0.0
        drift_note = "消费记录不足3天"

    # 6) 消费层级占比（按日均消费分位）
    summary_df = get_data_summary(BaseBody(
        college=base_body.college,
        major=base_body.major,
        grade=base_body.grade,
        className=base_body.className,
        studentId=base_body.studentId,
        timeBegin=time_begin,
        timeEnd=time_end,
    ))

    level_counts = {
        "低消费": 0,
        "较低消费": 0,
        "中消费": 0,
        "高消费": 0,
    }
    if not summary_df.empty:
        amount_cols = ["breakfast_avg_amount", "lunch_avg_amount", "dinner_avg_amount"]
        summary_df = summary_df.copy()
        summary_df["dailyAvg"] = summary_df[amount_cols].sum(axis=1)
        values = [float(v) for v in summary_df["dailyAvg"].tolist() if float(v) > 0]
        if values:
            q1 = float(np.quantile(values, 0.25))
            q2 = float(np.quantile(values, 0.50))
            q3 = float(np.quantile(values, 0.75))
            for v in values:
                if v <= q1:
                    level_counts["低消费"] += 1
                elif v <= q2:
                    level_counts["较低消费"] += 1
                elif v <= q3:
                    level_counts["中消费"] += 1
                else:
                    level_counts["高消费"] += 1

    # 7) GPA直方图（每个学生最新学期）
    gpa_sql = f"""
        SELECT bs.gpa
        FROM basic_data_score bs
        JOIN (
            SELECT student_id, MAX(term) AS term
            FROM basic_data_score
            GROUP BY student_id
        ) t ON t.student_id = bs.student_id AND t.term = bs.term
        JOIN basic_data_student s ON s.student_id = bs.student_id
        WHERE {where_sql}
    """
    cur.execute(gpa_sql, filter_params)
    gpa_values = [float(row[0]) for row in cur.fetchall() if row[0] is not None]

    gpa_bins = [0, 0, 0, 0, 0, 0]
    for g in gpa_values:
        if g < 2.0:
            gpa_bins[0] += 1
        elif g < 2.5:
            gpa_bins[1] += 1
        elif g < 3.0:
            gpa_bins[2] += 1
        elif g < 3.5:
            gpa_bins[3] += 1
        elif g <= 4.0:
            gpa_bins[4] += 1
        else:
            gpa_bins[5] += 1

    cur.close()
    conn.close()

    return {
        "statistics": {
            "totalStudents": total_students,
            "latest24hAmount": latest_24h_amount,
            "latest24hRecords": latest_24h_records,
        },
        "hourly": {
            "latestDay": latest_day,
            "amount": hourly_amount,
        },
        "levelDistribution": [
            {"name": "低消费", "value": level_counts["低消费"]},
            {"name": "较低消费", "value": level_counts["较低消费"]},
            {"name": "中消费", "value": level_counts["中消费"]},
            {"name": "高消费", "value": level_counts["高消费"]},
        ],
        "gpaHistogram": {
            "labels": ["<2.0", "2.0-2.5", "2.5-3.0", "3.0-3.5", "3.5-4.0", ">4.0"],
            "values": gpa_bins,
        },
        "drift": {
            "score": round(float(drift_score), 2),
            "hasData": drift_basis,
            "note": drift_note,
        },
        "meta": {
            "timeBegin": time_begin.isoformat(),
            "timeEnd": time_end.isoformat(),
            "dailySeriesCount": len(daily_series),
            "summaryStudentCount": int(len(summary_df)) if summary_df is not None else 0,
            "gpaSampleCount": len(gpa_values),
        },
    }


def normalize_student_id(value):
    """标准化学号字符串（去空白/去前导 0）。"""
    if value is None:
        return ""
    sid = str(value).strip()
    # 去前导 0，保持字符串
    sid = sid.lstrip("0") or "0"
    return sid


def get_cluster_details(student_ids: list[str], time_begin=None, time_end=None, include_llm: bool = False):
    """按学号批量返回画像详情，用于分页场景下的按页补全。"""
    if not student_ids:
        return []

    normalized_ids = []
    sid_seen = set()
    for sid in student_ids:
        sid_text = normalize_student_id(sid)
        if not sid_text or sid_text in sid_seen:
            continue
        sid_seen.add(sid_text)
        normalized_ids.append(sid_text)

    if not normalized_ids:
        return []

    conn = pymysql.connect(**mysql.DBCONFIG)
    cur = conn.cursor()

    gender_col = _resolve_student_gender_column(cur)

    sid_placeholders = ",".join(["%s"] * len(normalized_ids))

    # 学生基础信息
    student_sql = "SELECT student_id, name, college, major, class_name, grade"
    if gender_col:
        student_sql += f", {gender_col}"
    student_sql += f" FROM basic_data_student WHERE student_id IN ({sid_placeholders})"
    cur.execute(student_sql, normalized_ids)
    student_rows = cur.fetchall()

    student_map = {}
    for row in student_rows:
        sid_key = normalize_student_id(row[0])
        raw_gender = row[6] if gender_col and len(row) > 6 else None
        gender_text = "-"
        if raw_gender is not None:
            g = str(raw_gender).strip().upper()
            if g == "M":
                gender_text = "男"
            elif g == "F":
                gender_text = "女"
            else:
                gender_text = str(raw_gender)
        student_map[sid_key] = {
            "name": row[1] or "-",
            "college": row[2] or "-",
            "major": row[3] or "-",
            "className": row[4] or "-",
            "grade": row[5] or "-",
            "gender": gender_text
        }

    # 消费统计
    tx_sql = f"""
        SELECT
            student_id,
            COUNT(*) AS tx_count,
            SUM(amount) AS total_amount,
            MAX(amount) AS max_amount,
            MIN(amount) AS min_amount,
            COUNT(DISTINCT DATE_FORMAT(consumption_time, '%%Y-%%m')) AS month_span,
            SUM(CASE WHEN meal_type='早' THEN 1 ELSE 0 END) AS breakfast_cnt,
            SUM(CASE WHEN meal_type='中' THEN 1 ELSE 0 END) AS lunch_cnt,
            SUM(CASE WHEN meal_type='晚' THEN 1 ELSE 0 END) AS dinner_cnt,
            SUM(CASE WHEN meal_type NOT IN ('早','中','晚') OR meal_type IS NULL THEN 1 ELSE 0 END) AS night_cnt
        FROM consumption_data_students_consumption
        WHERE student_id IN ({sid_placeholders})
    """
    tx_params = list(normalized_ids)
    if time_begin and time_end:
        tx_sql += " AND consumption_time BETWEEN %s AND %s"
        tx_params.extend([time_begin, time_end])
    tx_sql += " GROUP BY student_id"
    cur.execute(tx_sql, tx_params)
    tx_rows = cur.fetchall()

    tx_map = {}
    for row in tx_rows:
        sid_key = normalize_student_id(row[0])
        tx_count = int(row[1] or 0)
        total_amount = float(row[2] or 0.0)
        max_amount = float(row[3] or 0.0)
        min_amount = float(row[4] or 0.0)
        month_span = int(row[5] or 0)
        if month_span <= 0:
            month_span = 1

        period_counts = {
            "早餐": int(row[6] or 0),
            "午餐": int(row[7] or 0),
            "晚餐": int(row[8] or 0),
            "夜宵": int(row[9] or 0)
        }
        peak_period = max(period_counts, key=period_counts.get) if tx_count else "-"
        tx_map[sid_key] = {
            "monthAvgCount": round(tx_count / month_span, 2),
            "monthAvgAmount": round(total_amount / month_span, 2),
            "monthTotalAmount": round(total_amount, 2),
            "singleMax": round(max_amount, 2),
            "singleMin": round(min_amount, 2),
            "peakPeriod": peak_period,
            "favoriteWindow": "-"
        }

    # 常去窗口
    win_sql = f"""
        SELECT student_id, window_id, COUNT(*) AS freq
        FROM consumption_data_students_consumption
        WHERE student_id IN ({sid_placeholders})
    """
    win_params = list(normalized_ids)
    if time_begin and time_end:
        win_sql += " AND consumption_time BETWEEN %s AND %s"
        win_params.extend([time_begin, time_end])
    win_sql += " GROUP BY student_id, window_id ORDER BY student_id, freq DESC"
    cur.execute(win_sql, win_params)
    win_rows = cur.fetchall()

    win_seen = set()
    for row in win_rows:
        sid_key = normalize_student_id(row[0])
        if sid_key in win_seen:
            continue
        win_seen.add(sid_key)
        tx_map.setdefault(sid_key, {
            "monthAvgCount": 0.0,
            "monthAvgAmount": 0.0,
            "monthTotalAmount": 0.0,
            "singleMax": 0.0,
            "singleMin": 0.0,
            "peakPeriod": "-",
            "favoriteWindow": "-"
        })
        tx_map[sid_key]["favoriteWindow"] = str(row[1]) if row[1] is not None else "-"

    # 最新 GPA
    gpa_sql = f"""
        SELECT bs.student_id, bs.gpa
        FROM basic_data_score bs
        JOIN (
            SELECT student_id, MAX(term) AS term
            FROM basic_data_score
            WHERE student_id IN ({sid_placeholders})
            GROUP BY student_id
        ) t ON t.student_id = bs.student_id AND t.term = bs.term
    """
    cur.execute(gpa_sql, normalized_ids)
    gpa_rows = cur.fetchall()
    gpa_map = {normalize_student_id(row[0]): round(float(row[1] or 0.0), 2) for row in gpa_rows}

    cur.close()
    conn.close()

    results = []
    for sid in normalized_ids:
        info = student_map.get(sid, {})
        tx = tx_map.get(sid, {
            "monthAvgCount": 0.0,
            "monthAvgAmount": 0.0,
            "monthTotalAmount": 0.0,
            "singleMax": 0.0,
            "singleMin": 0.0,
            "peakPeriod": "-",
            "favoriteWindow": "-"
        })
        row = {
            "studentId": sid,
            "name": info.get("name", "-"),
            "gender": info.get("gender", "-"),
            "college": info.get("college", "-"),
            "major": info.get("major", "-"),
            "className": info.get("className", "-"),
            "grade": info.get("grade", "-"),
            "gpa": gpa_map.get(sid, 0.0),
            "monthAvgCount": tx.get("monthAvgCount", 0.0),
            "monthAvgAmount": tx.get("monthAvgAmount", 0.0),
            "monthTotalAmount": tx.get("monthTotalAmount", 0.0),
            "singleMax": tx.get("singleMax", 0.0),
            "singleMin": tx.get("singleMin", 0.0),
            "peakPeriod": tx.get("peakPeriod", "-"),
            "favoriteWindow": tx.get("favoriteWindow", "-"),
            "llmExplanation": ""
        }
        results.append(row)

    if include_llm and len(results) <= 20:
        for row in results:
            try:
                row["llmExplanation"] = build_student_portrait_explanation(row) or ""
            except Exception:
                row["llmExplanation"] = ""

    return results

def analysis_cluster(cluster_body:ClusterBody):
    """消费聚类分析：生成簇中心、样本标签、分布数据与图表点位。"""
    page = int(cluster_body.page or 1)
    page_size = int(cluster_body.pageSize or 20)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    page_size = min(page_size, 200)

    df = get_data_summary(cluster_body)
    if df.empty:
        return {
            "centers": [],
            "data": [],
            "results": [],
            "clusterData": [],
            "distributionData": [],
            "total": 0,
            "page": page,
            "pageSize": page_size
        }

    # 学号查询时，聚类建模应基于同筛选群体而不是单个学生，否则会退化成单样本单簇。
    model_df = df
    if cluster_body.studentId:
        cohort_body = cluster_body.model_copy(update={"studentId": None, "includeDetails": False, "page": 1, "pageSize": 20})
        cohort_df = get_data_summary(cohort_body)
        if not cohort_df.empty:
            model_df = cohort_df

    # 计算日均消费与日均次数
    amount_cols = ["breakfast_avg_amount", "lunch_avg_amount", "dinner_avg_amount"]
    count_cols = ["breakfast_avg_count", "lunch_avg_count", "dinner_avg_count"]
    model_df["dailyAvg"] = model_df[amount_cols].sum(axis=1)
    model_df["dailyCount"] = model_df[count_cols].sum(axis=1)

    feature_df = model_df[["dailyAvg", "dailyCount"]].copy()
    min_max_scaler = MinMaxScaler()
    scalared_df = min_max_scaler.fit_transform(feature_df)

    # 兼容 n_clusters / clusterNums 字段
    n_samples = len(model_df)
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

    model_df["label"] = labels

    if cluster_body.studentId:
        sid_norm = normalize_student_id(cluster_body.studentId)
        df = model_df[model_df.index.to_series().astype(str).apply(normalize_student_id) == sid_norm].copy()
        if df.empty:
            df = get_data_summary(cluster_body)
            if df.empty:
                return {
                    "centers": centers_df.to_dict(orient="records"),
                    "data": [],
                    "results": [],
                    "clusterData": [],
                    "distributionData": [],
                    "llmSummary": None,
                    "llmStudentExplanations": {},
                    "total": 0,
                    "page": 1,
                    "pageSize": page_size
                }
            df["dailyAvg"] = df[amount_cols].sum(axis=1)
            df["dailyCount"] = df[count_cols].sum(axis=1)
            # 兜底：按中心最近邻确定标签，避免无标签导致前端分层异常。
            fallback_feature = df[["dailyAvg", "dailyCount"]].copy()
            fallback_scaled = min_max_scaler.transform(fallback_feature)
            fallback_labels = []
            for vec in fallback_scaled:
                dists = np.sum((centers - vec) ** 2, axis=1)
                fallback_labels.append(int(np.argmin(dists)))
            df["label"] = fallback_labels

    # 轻量模式：用于首页等只需要聚类占比/散点的场景，避免大范围全量明细查询导致变慢
    detail_mode = bool(cluster_body.includeDetails) or bool(cluster_body.studentId)

    # 聚类类型命名（按日均消费排序）
    center_order = centers_df["dailyAvg"].sort_values().index.tolist()
    type_names = ["低消费", "较低消费", "中消费", "高消费", "高消费2", "高消费3"]
    label_to_type = {}
    for rank, label_idx in enumerate(center_order):
        label_to_type[label_idx] = type_names[min(rank, len(type_names)-1)]

    if not detail_mode:
        results = []
        cluster_points = []
        distribution_count = {}

        for sid, row in df.iterrows():
            sid_str = str(sid).strip()
            daily = float(row["dailyAvg"])
            daily_count = float(row["dailyCount"])
            label = int(row["label"])
            cluster_type = label_to_type.get(label, "普通消费")

            results.append({
                "studentId": sid_str,
                "dailyAvg": round(daily, 2),
                "dailyCount": round(daily_count, 2),
                "clusterType": cluster_type,
                "consumptionType": cluster_type,
                "consumptionGroup": cluster_type
            })

            cluster_points.append({
                "x": round(daily, 2),
                "y": round(daily_count, 2),
                "label": cluster_type,
                "studentId": sid_str
            })
            distribution_count[cluster_type] = distribution_count.get(cluster_type, 0) + 1

        distribution_data = [{"name": k, "value": v} for k, v in distribution_count.items()]
        return {
            "centers": centers_df.to_dict(orient="records"),
            "data": feature_df.to_dict(orient="records"),
            "results": results,
            "clusterData": cluster_points,
            "distributionData": distribution_data,
            "llmSummary": None,
            "llmStudentExplanations": {},
            "total": len(results),
            "page": 1,
            "pageSize": len(results)
        }

    all_sid_values = [str(i).strip() for i in df.index.tolist()]
    if cluster_body.studentId:
        sid_values = [str(cluster_body.studentId).strip()]
    else:
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        sid_values = all_sid_values[start_index:end_index]

    def default_tx_stats():
        return {
            "monthAvgCount": 0.0,
            "monthAvgAmount": 0.0,
            "monthTotalAmount": 0.0,
            "singleMax": 0.0,
            "singleMin": 0.0,
            "peakPeriod": "-",
            "favoriteWindow": "-"
        }

    student_map = {}
    tx_stats_map = {}
    gpa_map = {}
    if sid_values:
        conn = pymysql.connect(**mysql.DBCONFIG)
        cur = conn.cursor()
        sid_set = set(normalize_student_id(i) for i in sid_values)
        use_all_scope = (
            len(sid_values) > 1000
            and not cluster_body.studentId
            and not cluster_body.college
            and not cluster_body.major
            and not cluster_body.grade
            and not cluster_body.className
        )

        # 拉取学生基础信息（含可选 gender/sex）
        cur.execute("SHOW COLUMNS FROM basic_data_student")
        student_columns = {row[0] for row in cur.fetchall()}
        gender_col = "gender" if "gender" in student_columns else ("sex" if "sex" in student_columns else None)

        sid_placeholders = ",".join(["%s"] * len(sid_values))
        student_sql = "SELECT student_id, name, college, major, class_name, grade"
        if gender_col:
            student_sql += f", {gender_col}"
        student_sql += " FROM basic_data_student"
        if use_all_scope:
            cur.execute(student_sql)
        else:
            student_sql += f" WHERE student_id IN ({sid_placeholders})"
            cur.execute(student_sql, sid_values)
        student_rows = cur.fetchall()

        for row in student_rows:
            sid_key = normalize_student_id(row[0])
            if not sid_key:
                continue
            if sid_key not in sid_set:
                continue
            raw_gender = row[6] if gender_col and len(row) > 6 else None
            gender_text = "-"
            if raw_gender is not None:
                gender_upper = str(raw_gender).strip().upper()
                if gender_upper == "M":
                    gender_text = "男"
                elif gender_upper == "F":
                    gender_text = "女"
                else:
                    gender_text = str(raw_gender)

            student_map[sid_key] = {
                "name": row[1] or "-",
                "college": row[2] or "-",
                "major": row[3] or "-",
                "className": row[4] or "-",
                "grade": row[5] or "-",
                "gender": gender_text
            }

        # 拉取消费统计（平均月消费次数、平均月消费金额、极值、高峰餐别）
        tx_sql = """
            SELECT
                student_id,
                COUNT(*) AS tx_count,
                SUM(amount) AS total_amount,
                MAX(amount) AS max_amount,
                MIN(amount) AS min_amount,
                COUNT(DISTINCT DATE_FORMAT(consumption_time, '%%Y-%%m')) AS month_span,
                SUM(CASE WHEN meal_type='早' THEN 1 ELSE 0 END) AS breakfast_cnt,
                SUM(CASE WHEN meal_type='中' THEN 1 ELSE 0 END) AS lunch_cnt,
                SUM(CASE WHEN meal_type='晚' THEN 1 ELSE 0 END) AS dinner_cnt,
                SUM(CASE WHEN meal_type NOT IN ('早','中','晚') OR meal_type IS NULL THEN 1 ELSE 0 END) AS night_cnt
            FROM consumption_data_students_consumption
            WHERE 1=1
        """
        tx_params = []
        if not use_all_scope:
            tx_sql += f" AND student_id IN ({sid_placeholders})"
            tx_params.extend(sid_values)
        if cluster_body.timeBegin and cluster_body.timeEnd:
            tx_sql += " AND consumption_time BETWEEN %s AND %s"
            tx_params.extend([cluster_body.timeBegin, cluster_body.timeEnd])
        tx_sql += " GROUP BY student_id"
        cur.execute(tx_sql, tx_params)
        tx_rows = cur.fetchall()
        for row in tx_rows:
            sid_key = normalize_student_id(row[0])
            if sid_key not in sid_set:
                continue
            tx_count = int(row[1] or 0)
            total_amount = float(row[2] or 0.0)
            max_amount = float(row[3] or 0.0)
            min_amount = float(row[4] or 0.0)
            month_span = int(row[5] or 0)
            if month_span <= 0:
                month_span = 1
            breakfast_cnt = int(row[6] or 0)
            lunch_cnt = int(row[7] or 0)
            dinner_cnt = int(row[8] or 0)
            night_cnt = int(row[9] or 0)

            period_counts = {
                "早餐": breakfast_cnt,
                "午餐": lunch_cnt,
                "晚餐": dinner_cnt,
                "夜宵": night_cnt
            }
            peak_period = max(period_counts, key=period_counts.get) if tx_count else "-"
            tx_stats_map[sid_key] = {
                "monthAvgCount": round(tx_count / month_span, 2),
                "monthAvgAmount": round(total_amount / month_span, 2),
                "monthTotalAmount": round(total_amount, 2),
                "singleMax": round(max_amount, 2),
                "singleMin": round(min_amount, 2),
                "peakPeriod": peak_period,
                "favoriteWindow": "-"
            }

        # 拉取最常去窗口
        win_sql = """
            SELECT student_id, window_id, COUNT(*) AS freq
            FROM consumption_data_students_consumption
            WHERE 1=1
        """
        win_params = []
        if not use_all_scope:
            win_sql += f" AND student_id IN ({sid_placeholders})"
            win_params.extend(sid_values)
        if cluster_body.timeBegin and cluster_body.timeEnd:
            win_sql += " AND consumption_time BETWEEN %s AND %s"
            win_params.extend([cluster_body.timeBegin, cluster_body.timeEnd])
        win_sql += " GROUP BY student_id, window_id ORDER BY student_id, freq DESC"
        cur.execute(win_sql, win_params)
        win_rows = cur.fetchall()
        seen = set()
        for row in win_rows:
            sid_key = normalize_student_id(row[0])
            if sid_key not in sid_set:
                continue
            if sid_key in seen:
                continue
            seen.add(sid_key)
            if sid_key not in tx_stats_map:
                tx_stats_map[sid_key] = default_tx_stats()
            tx_stats_map[sid_key]["favoriteWindow"] = str(row[1]) if row[1] is not None else "-"

        # 拉取最新学期 GPA
        gpa_sql = """
            SELECT bs.student_id, bs.gpa
            FROM basic_data_score bs
            JOIN (
                SELECT student_id, MAX(term) AS term
                FROM basic_data_score
                GROUP BY student_id
            ) t ON t.student_id = bs.student_id AND t.term = bs.term
        """
        if use_all_scope:
            cur.execute(gpa_sql)
        else:
            gpa_sql = f"""
                SELECT bs.student_id, bs.gpa
                FROM basic_data_score bs
                JOIN (
                    SELECT student_id, MAX(term) AS term
                    FROM basic_data_score
                    WHERE student_id IN ({sid_placeholders})
                    GROUP BY student_id
                ) t ON t.student_id = bs.student_id AND t.term = bs.term
            """
            cur.execute(gpa_sql, sid_values)
        gpa_rows = cur.fetchall()
        for row in gpa_rows:
            sid_key = normalize_student_id(row[0])
            if sid_key not in sid_set:
                continue
            gpa_map[sid_key] = round(float(row[1] or 0.0), 2)

        cur.close()
        conn.close()

    results = []
    cluster_points = []
    distribution_count = {}

    for sid, row in df.iterrows():
        sid_str = str(sid).strip()
        sid_key = normalize_student_id(sid_str)
        info = student_map.get(sid_key, {})
        tx_stats = tx_stats_map.get(sid_key, default_tx_stats())
        name = info.get("name", "-")
        college = info.get("college", "-")
        major = info.get("major", "-")
        class_name = info.get("className", "-")
        grade = info.get("grade", "-")
        gender = info.get("gender", "-")
        daily = float(row["dailyAvg"])
        daily_count = float(row["dailyCount"])
        label = int(row["label"])
        cluster_type = label_to_type.get(label, "普通消费")

        gpa_val = float(gpa_map.get(sid_key, 0.0))

        results.append({
            "studentId": sid_str,
            "name": name,
            "gender": gender,
            "college": college,
            "major": major,
            "className": class_name,
            "grade": grade,
            "monthlyAvg": round(daily, 2),
            "dailyAvg": round(daily, 2),
            "dailyCount": round(daily_count, 2),
            "gpa": round(gpa_val, 2),
            "monthAvgCount": tx_stats.get("monthAvgCount", 0.0),
            "monthAvgAmount": tx_stats.get("monthAvgAmount", 0.0),
            "monthTotalAmount": tx_stats.get("monthTotalAmount", 0.0),
            "singleMax": tx_stats.get("singleMax", 0.0),
            "singleMin": tx_stats.get("singleMin", 0.0),
            "peakPeriod": tx_stats.get("peakPeriod", "-"),
            "favoriteWindow": tx_stats.get("favoriteWindow", "-"),
            "clusterType": cluster_type,
            "consumptionType": cluster_type,
            "consumptionGroup": cluster_type
        })

        cluster_points.append({
            "x": round(daily, 2),
            "y": round(daily_count, 2),
            "label": cluster_type,
            "studentId": sid_str,
            "name": name,
            "college": college,
            "major": major,
            "className": class_name,
            "grade": grade,
            "gender": gender
        })

        distribution_count[cluster_type] = distribution_count.get(cluster_type, 0) + 1

    distribution_data = [
        {"name": k, "value": v} for k, v in distribution_count.items()
    ]

    # 可选：大模型解释层（不参与标签判定，失败自动降级）
    llm_summary = None
    llm_student_explanations = {}
    try:
        sample_size = int(len(results))
        low_count = int(distribution_count.get("低消费", 0))
        low_ratio = round((low_count / sample_size) * 100, 2) if sample_size else 0.0
        llm_summary = build_cluster_summary_explanation({
            "sampleSize": sample_size,
            "distribution": distribution_data,
            "lowRatio": low_ratio,
        })

        # 控制调用成本：仅在样本较小时生成个体解释，避免全量卡顿
        if len(results) <= 80:
            for row in results[:30]:
                text = build_student_portrait_explanation(row)
                if text:
                    llm_student_explanations[str(row.get("studentId", ""))] = text
    except Exception:
        llm_summary = None
        llm_student_explanations = {}

    for row in results:
        sid = str(row.get("studentId", ""))
        row["llmExplanation"] = llm_student_explanations.get(sid) or ""

    total_count = len(results)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paged_results = results[start_index:end_index]

    max_scatter_points = 1600
    if len(cluster_points) > max_scatter_points:
        step = max(1, len(cluster_points) // max_scatter_points)
        sampled_cluster_points = cluster_points[::step][:max_scatter_points]
    else:
        sampled_cluster_points = cluster_points

    return {
        "centers": centers_df.to_dict(orient="records"),
        "data": feature_df.to_dict(orient="records"),
        "results": paged_results,
        "clusterData": sampled_cluster_points,
        "distributionData": distribution_data,
        "llmSummary": llm_summary,
        "llmStudentExplanations": llm_student_explanations,
        "total": total_count,
        "page": page,
        "pageSize": page_size
    }

def analysis_drift(drift_body:DriftBody):
    """消费漂移检测：基于滑动窗口比较分布差异并计算置信度。"""
    # 1-30 日
    # 1-8 (val1) 8-15 (val2) 15-22 (val3) 22-29
    time_begin = drift_body.timeBegin or drift_body.start_date
    time_end = drift_body.timeEnd or drift_body.end_date
    time_window = int(drift_body.timeWindow or 7)
    p_threshold = float(drift_body.pThreshold or 0.05)

    if p_threshold < 0.01 or p_threshold > 0.1:
        raise HTTPException(status_code=400, detail="阈值范围必须在 0.01 到 0.1 之间")

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
    # 步长与时间窗口一致：按完整窗口推进，避免不同窗口下出现高度重叠的“近似 7 天”观感
    step_days = time_window

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

        # 数据为空或样本过少时，跳过模型以加速并避免异常
        if df_left.empty or df_right.empty or data_train.shape[0] < 2 or data_test.shape[0] < 1:
            p = 1.0
        else:
            min_max_scalar = MinMaxScaler()
            data_train = min_max_scalar.fit_transform(data_train)
            data_test = min_max_scalar.transform(data_test)

            # 动态缩小簇数以降低计算量
            dynamic_k = max(5, int(np.sqrt(data_train.shape[0])))
            dynamic_k = min(dynamic_k, 20)
            model = EIkMeans(dynamic_k)
            model.build_partition(data_train,data_test.shape[0])
            p = model.drift_detection2(data_test, p_threshold)
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
        consumption_drift_points.append(round(float(right_daily), 2) if p < p_threshold else None)

        # 生成表格结果：对每个学生计算漂移前后均值
        common_ids = df_left.index.intersection(df_right.index)
        detect_date = right_time

        # 单体漂移：仅针对指定学号
        if drift_body.studentId:
            sid_str = str(drift_body.studentId)
            before_mean = float(df_left.loc[sid_str].mean()) if sid_str in df_left.index else 0.0
            after_mean = float(df_right.loc[sid_str].mean()) if sid_str in df_right.index else 0.0
            change_rate = float(after_mean - before_mean) / abs(before_mean + 1e-9) * 100 if before_mean != 0 else 0.0
            info = name_cache.get(sid_str, {})
            results.append({
                "studentId": sid_str,
                "name": info.get("name", "-"),
                "college": drift_body.college or info.get("college", "-"),
                "beforeDrift": round(before_mean, 2),
                "afterDrift": round(after_mean, 2),
                "changeRate": round(change_rate, 2),
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
                info = name_cache.get(sid_str, {})
                results.append({
                    "studentId": sid_str,
                    "name": info.get("name", "-"),
                    "college": drift_body.college or info.get("college", "-"),
                    "beforeDrift": round(before_mean, 2),
                    "afterDrift": round(after_mean, 2),
                    "changeRate": round(change_rate, 2),
                    "detectDate": detect_date.isoformat()
                })

        dates.append(detect_date.isoformat())
        middle_time += timedelta(days=step_days)
        right_time += timedelta(days=step_days)
        left_time += timedelta(days=step_days)
        idx += 1
        df_left = df_right

    return {
        "p_values": p_values,
        "p_threshold": p_threshold,
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
    # 汇总消费数据（群体口径：不按 studentId 过滤，避免把群体缩成单个学生）
    summary_df = get_data_summary(BaseBody(
        college=correlation_body.college,
        major=correlation_body.major,
        grade=correlation_body.grade,
        className=correlation_body.className,
        studentId=None,
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

    # 取每个学生的最新学期 GPA（群体口径：不按 studentId 过滤）
    where_sql = " WHERE 1=1"
    params = []
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

    def calc_corr_ci(corr_value: float, n: int):
        if n <= 3:
            return None, None
        corr_value = max(min(float(corr_value), 0.999999), -0.999999)
        z = np.arctanh(corr_value)
        z_se = 1.0 / np.sqrt(n - 3)
        z_crit = stats.norm.ppf(0.975)
        low = np.tanh(z - z_crit * z_se)
        high = np.tanh(z + z_crit * z_se)
        return float(low), float(high)

    def bh_fdr_adjust(p_values: list[float]) -> list[float]:
        m = len(p_values)
        if m == 0:
            return []
        indexed = sorted(list(enumerate(p_values)), key=lambda item: item[1])
        adjusted = [1.0] * m
        prev = 1.0
        for rank in range(m, 0, -1):
            original_index, p_val = indexed[rank - 1]
            val = min(prev, (float(p_val) * m) / rank)
            adjusted[original_index] = float(min(max(val, 0.0), 1.0))
            prev = val
        return adjusted

    sample_size = int(len(merged))
    factor_map = {
        "breakfast_avg_amount": "早餐均额",
        "lunch_avg_amount": "午餐均额",
        "dinner_avg_amount": "晚餐均额",
        "dailyAvg": "日均消费",
        "monthlyAvg": "月均消费"
    }
    results = []
    p_values = []
    for col, label in factor_map.items():
        series = merged[col]
        if series.nunique() < 2 or merged["gpa"].nunique() < 2:
            corr, p = 0.0, 1.0
        else:
            if method == "spearman":
                corr, p = stats.spearmanr(series, merged["gpa"])
            elif method == "pearson":
                corr, p = stats.pearsonr(series, merged["gpa"])
            else:
                raise HTTPException(status_code=400, detail="不支持的相关性方法")
        if np.isnan(corr) or np.isnan(p):
            corr, p = 0.0, 1.0

        ci_low, ci_high = calc_corr_ci(corr, sample_size)
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
            "ciLower": ci_low,
            "ciUpper": ci_high,
            "sampleSize": sample_size,
            "interpretation": interp
        })
        p_values.append(float(p))

    q_values = bh_fdr_adjust(p_values)
    for index, result_row in enumerate(results):
        q_val = q_values[index] if index < len(q_values) else 1.0
        result_row["qValue"] = float(q_val)
        result_row["significance"] = "显著" if q_val < 0.05 else "不显著"

    def classify_peak_period(tx_df: pd.DataFrame) -> str:
        if tx_df is None or tx_df.empty:
            return "-"
        periods = {"早": 0, "中": 0, "晚": 0, "夜宵": 0}
        for _, tx in tx_df.iterrows():
            ts = tx.get("consumption_time")
            meal = str(tx.get("meal_type") or "").strip()
            label = None
            if meal in ("早", "中", "晚"):
                label = meal
            else:
                hour = None
                if isinstance(ts, datetime):
                    hour = ts.hour
                elif ts is not None:
                    try:
                        hour = pd.to_datetime(ts).hour
                    except Exception:
                        hour = None
                if hour is not None:
                    if 6 <= hour < 10:
                        label = "早"
                    elif 10 <= hour < 15:
                        label = "中"
                    elif 15 <= hour < 21:
                        label = "晚"
                    else:
                        label = "夜宵"
            if label is None:
                label = "夜宵"
            periods[label] += 1
        peak_count = max(periods.values()) if periods else 0
        if peak_count <= 0:
            return "-"
        peak_labels = [k for k, v in periods.items() if v == peak_count]
        return "/".join(peak_labels)

    def calc_stability(tx_df: pd.DataFrame) -> dict:
        if tx_df is None or tx_df.empty:
            return {
                "stabilityText": "数据不足",
                "volatility": None,
                "isRegular": None
            }

        daily = tx_df.copy()
        daily["consumption_time"] = pd.to_datetime(daily["consumption_time"], errors="coerce")
        daily = daily.dropna(subset=["consumption_time"])
        if daily.empty:
            return {
                "stabilityText": "数据不足",
                "volatility": None,
                "isRegular": None
            }

        daily["dt"] = daily["consumption_time"].dt.date
        daily_amount = daily.groupby("dt")["amount"].sum()
        mean_val = float(daily_amount.mean()) if len(daily_amount) else 0.0
        std_val = float(daily_amount.std(ddof=0)) if len(daily_amount) else 0.0

        if mean_val <= 0:
            cv = 0.0
        else:
            cv = std_val / mean_val

        is_regular = cv < 0.5
        if cv < 0.25:
            level = "低波动"
        elif cv < 0.5:
            level = "中波动"
        else:
            level = "高波动"

        regular_text = "规律" if is_regular else "不规律"
        return {
            "stabilityText": f"{level}（波动系数 {cv:.2f}，{regular_text}）",
            "volatility": round(cv, 4),
            "isRegular": is_regular
        }

    student_profile = None
    student_point = None
    if correlation_body.studentId:
        sid = normalize_student_id(correlation_body.studentId)

        # 学生个人消费：单独按学号聚合，避免依赖 merged 命中导致 0 值
        student_summary_df = get_data_summary(BaseBody(
            college=correlation_body.college,
            major=correlation_body.major,
            grade=correlation_body.grade,
            className=correlation_body.className,
            studentId=correlation_body.studentId,
            timeBegin=time_begin,
            timeEnd=time_end
        ))

        if not student_summary_df.empty:
            student_summary_df["dailyAvg"] = student_summary_df[meal_cols].sum(axis=1)
            student_summary_df["monthlyAvg"] = student_summary_df["dailyAvg"] * 30
            profile_cons = student_summary_df.iloc[0]
            daily_avg_val = float(profile_cons.get("dailyAvg", 0.0))
            monthly_avg_val = float(profile_cons.get("monthlyAvg", 0.0))
        else:
            # 兜底：尝试在群体汇总中按规范化学号匹配
            try:
                summary_row = summary_df[summary_df["norm_id"] == sid]
                profile_cons = summary_row.iloc[0] if len(summary_row) > 0 else None
            except Exception:
                profile_cons = None
            daily_avg_val = float(profile_cons.get("dailyAvg", 0.0)) if profile_cons is not None else 0.0
            monthly_avg_val = float(profile_cons.get("monthlyAvg", 0.0)) if profile_cons is not None else 0.0

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
                return "中消费"
            return "高消费"

        # 扩展画像：消费高峰、稳定性、单笔极值、常去窗口、月度指标
        tx_sql = """
            SELECT amount, meal_type, window_id, consumption_time
            FROM consumption_data_students_consumption
            WHERE student_id=%s
        """
        tx_params = [correlation_body.studentId]
        if time_begin and time_end:
            tx_sql += " AND consumption_time BETWEEN %s AND %s"
            tx_params.extend([time_begin, time_end])

        conn = pymysql.connect(**mysql.DBCONFIG)
        cur = conn.cursor()
        try:
            # 学生绩点：独立查询，避免因消费缺失导致绩点被错误置为 0
            if term:
                cur.execute(
                    "SELECT gpa, term FROM basic_data_score WHERE student_id=%s AND term=%s ORDER BY term DESC LIMIT 1",
                    (correlation_body.studentId, term)
                )
                grow = cur.fetchone()
                if not grow:
                    cur.execute(
                        "SELECT gpa, term FROM basic_data_score WHERE student_id=%s ORDER BY term DESC LIMIT 1",
                        (correlation_body.studentId,)
                    )
                    grow = cur.fetchone()
            else:
                cur.execute(
                    "SELECT gpa, term FROM basic_data_score WHERE student_id=%s ORDER BY term DESC LIMIT 1",
                    (correlation_body.studentId,)
                )
                grow = cur.fetchone()

            cur.execute(tx_sql, tx_params)
            tx_rows = cur.fetchall()

            gender_col = _resolve_student_gender_column(cur)
            student_sql = "SELECT student_id, name, college, major, class_name, grade"
            if gender_col:
                student_sql += f", {gender_col}"
            student_sql += " FROM basic_data_student WHERE student_id=%s"
            cur.execute(student_sql, (correlation_body.studentId,))
            srow = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        gpa_val = float(grow[0]) if grow else 0.0

        tx_df = pd.DataFrame(tx_rows, columns=["amount", "meal_type", "window_id", "consumption_time"]) if tx_rows else pd.DataFrame(columns=["amount", "meal_type", "window_id", "consumption_time"])
        if not tx_df.empty:
            tx_df["amount"] = pd.to_numeric(tx_df["amount"], errors="coerce").fillna(0.0)
            tx_df["consumption_time"] = pd.to_datetime(tx_df["consumption_time"], errors="coerce")

        tx_count = int(len(tx_df))

        monthly_totals = pd.Series(dtype=float)
        monthly_counts = pd.Series(dtype=float)
        if not tx_df.empty:
            valid_tx = tx_df.dropna(subset=["consumption_time"]).copy()
            if not valid_tx.empty:
                valid_tx["month"] = valid_tx["consumption_time"].dt.to_period("M")
                monthly_totals = valid_tx.groupby("month")["amount"].sum()
                monthly_counts = valid_tx.groupby("month")["amount"].count()

        avg_month_total = float(monthly_totals.mean()) if len(monthly_totals) else 0.0
        avg_month_count = float(monthly_counts.mean()) if len(monthly_counts) else 0.0
        avg_month_amount = (avg_month_total / avg_month_count) if avg_month_count > 0 else 0.0

        max_amount = float(tx_df["amount"].max()) if tx_count else 0.0
        min_amount = float(tx_df["amount"].min()) if tx_count else 0.0

        favorite_window = "-"
        if tx_count and "window_id" in tx_df.columns:
            window_counts = tx_df["window_id"].dropna().astype(str).value_counts()
            if len(window_counts):
                favorite_window = str(window_counts.index[0])

        peak_period = classify_peak_period(tx_df)
        stability = calc_stability(tx_df)

        gender_val = "-"
        if srow and len(srow) >= 7:
            raw_gender = srow[6]
            if raw_gender is not None:
                g = str(raw_gender).strip().upper()
                if g == "M":
                    gender_val = "男"
                elif g == "F":
                    gender_val = "女"
                else:
                    gender_val = str(raw_gender)

        student_profile = {
            "studentId": str(correlation_body.studentId),
            "name": srow[1] if srow else "-",
            "gender": gender_val,
            "college": srow[2] if srow else "-",
            "major": srow[3] if srow else "-",
            "className": srow[4] if srow else "-",
            "grade": srow[5] if srow else "-",
            "gpa": gpa_val,
            "dailyAvg": daily_avg_val,
            "monthlyAvg": monthly_avg_val,
            "monthAvgCount": round(avg_month_count, 2),
            "monthAvgAmount": round(avg_month_amount, 2),
            "monthTotalAmount": round(avg_month_total, 2),
            "peakPeriod": peak_period,
            "stability": stability.get("stabilityText"),
            "stabilityVolatility": stability.get("volatility"),
            "isRegular": stability.get("isRegular"),
            "singleMax": round(max_amount, 2),
            "singleMin": round(min_amount, 2),
            "favoriteWindow": favorite_window,
            "consumptionType": classify_group(daily_avg_val),
            "consumptionGroup": classify_group(daily_avg_val)
        }
        student_point = {
            "dailyAvg": round(float(daily_avg_val or 0.0), 2),
            "gpa": round(float(gpa_val or 0.0), 2),
            "studentId": str(correlation_body.studentId)
        }

    return {
        "scatterData": scatter_data,
        "correlationResults": results,
        "studentProfile": student_profile,
        "studentPoint": student_point,
        "meta": {
            "consumptionCount": int(len(summary_df)),
            "gpaCount": int(len(gpa_df)),
            "mergedCount": int(len(merged)),
            "avgDaily": float(merged["dailyAvg"].mean()),
            "avgGpa": float(merged["gpa"].mean()),
            "sampleSize": sample_size,
            "termUsed": term_used,
            "method": method,
            "multipleTest": "BH-FDR",
            "fallback": fallback_msg if fallback_msg else None
        }
    }
