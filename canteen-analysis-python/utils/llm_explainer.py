"""可选大模型解释层：用于对既有标签结果做自然语言解释，不参与标签判定。"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


def _to_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def is_llm_enabled() -> bool:
    """通过环境变量开关控制，默认关闭。"""
    return _to_bool(os.getenv("LLM_EXPLAINER_ENABLED", "false"))


def _get_runtime_config() -> dict[str, Any]:
    return {
        "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "model": os.getenv("LLM_MODEL", "openai/gpt-4.1-mini").strip(),
        "timeout": float(os.getenv("LLM_TIMEOUT", "8")),
    }


def _call_chat_api(prompt: str) -> Optional[str]:
    cfg = _get_runtime_config()
    if not cfg["api_key"]:
        return None

    url = f"{cfg['base_url']}/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是校园消费数据分析助手。"
                    "请仅根据给定结构化数据生成解释，不改变已有标签，不臆造事实。"
                    "输出要具体，优先给出口径说明、关键特征、趋势判断和可执行建议，"
                    "并明确结论仅反映消费行为画像，不代表行政认定。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 420,
    }

    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return (
                body.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError):
        # 降级为无解释，避免影响主流程
        return None


def build_student_portrait_explanation(student: dict[str, Any]) -> Optional[str]:
    """生成学生画像解释文本；失败返回 None。"""
    if not is_llm_enabled():
        return None

    prompt = (
        "请根据以下画像字段生成180-260字中文解释，保持中性客观，不更改任何标签名。"
        "输出结构：1) 先总结消费层级与活跃度；2) 解释金额、频次、高峰餐别与窗口偏好；"
        "3) 给出2-3条可执行建议（预算、作息、餐次结构）；4) 明确仅为消费行为画像，不代表行政认定。\\n"
        f"姓名: {student.get('name', '-')}; 学号: {student.get('studentId', '-')}; "
        f"学院: {student.get('college', '-')}; 专业: {student.get('major', '-')}; "
        f"日均消费: {student.get('dailyAvg', '-')}; 月均消费次数: {student.get('monthAvgCount', '-')}; "
        f"月均消费额: {student.get('monthAvgAmount', '-')}; 绩点: {student.get('gpa', '-')}; "
        f"消费高峰: {student.get('peakPeriod', '-')}; 稳定性: {student.get('stability', '-')}; "
        f"最常去窗口: {student.get('favoriteWindow', '-')}; 标签: {student.get('clusterType', '-')}."
    )
    return _call_chat_api(prompt)


def build_cluster_summary_explanation(summary: dict[str, Any]) -> Optional[str]:
    """生成群体聚类结果解释文本；失败返回 None。"""
    if not is_llm_enabled():
        return None

    prompt = (
        "请基于下列聚类统计，输出200-300字中文分析摘要。"
        "内容应包含：消费分层结构、各层级比例、整体离散程度、可能的管理启示与注意事项；"
        "保持中性客观，不改变标签，不做价值判断。\\n"
        f"样本总数: {summary.get('sampleSize', 0)}; "
        f"分布: {summary.get('distribution', [])}; "
        f"低消费占比: {summary.get('lowRatio', 0)}%。"
    )
    return _call_chat_api(prompt)


def build_custom_explanation(prompt: str) -> Optional[str]:
    """通用解释入口：由上层传入 prompt，失败返回 None。"""
    if not prompt:
        return None
    if not is_llm_enabled():
        return None
    return _call_chat_api(prompt)
