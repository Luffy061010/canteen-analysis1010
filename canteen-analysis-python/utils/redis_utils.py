"""Redis 读写封装：用于缓存与 token 黑名单。"""
import json

import redis
from config.redis import REDISCONFIG

r = redis.Redis(**REDISCONFIG, decode_responses=True)

def set_key(key, value):
    """写入字符串键值（Redis 不可用时忽略）。"""
    try:
        r.set(key, value)
    except Exception:
        return None

def get_key(key):
    """读取字符串键值（Redis 不可用时返回 None）。"""
    try:
        return r.get(key)
    except Exception:
        return None