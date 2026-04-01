"""Redis 读写封装：用于缓存与 token 黑名单。"""
import json
import os

import redis
from config.redis import REDISCONFIG

REDIS_ENABLED = os.getenv("REDIS_ENABLED", "1") not in {"0", "false", "False", "no", "NO"}
r = redis.Redis(**REDISCONFIG, decode_responses=True) if REDIS_ENABLED else None

def set_key(key, value, ex=None):
    """写入字符串键值（Redis 不可用时忽略）。支持可选过期秒数 ex。"""
    if not REDIS_ENABLED or r is None:
        return None
    try:
        if ex is not None:
            r.set(key, value, ex=ex)
        else:
            r.set(key, value)
    except Exception:
        return None

def get_key(key):
    """读取字符串键值（Redis 不可用时返回 None）。"""
    if not REDIS_ENABLED or r is None:
        return None
    try:
        return r.get(key)
    except Exception:
        return None