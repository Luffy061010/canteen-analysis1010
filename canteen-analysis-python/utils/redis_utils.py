"""Redis 读写封装：用于缓存与 token 黑名单。"""
import json

import redis
from config.redis import REDISCONFIG

r = redis.Redis(**REDISCONFIG, decode_responses=True)

def set_key(key, value, ex=None):
    """写入字符串键值（Redis 不可用时忽略）。支持可选过期秒数 ex。"""
    try:
        if ex is not None:
            r.set(key, value, ex=ex)
        else:
            r.set(key, value)
    except Exception:
        return None

def get_key(key):
    """读取字符串键值（Redis 不可用时返回 None）。"""
    try:
        return r.get(key)
    except Exception:
        return None