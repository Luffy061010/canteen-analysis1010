import json

import redis
from config.redis import REDISCONFIG

r = redis.Redis(**REDISCONFIG,decode_responses=True)

def set_key(key, value):
    r.set(key,value)

def get_key(key):
    return r.get(key)

dict = {
    "1":1,
    "2":2
}
r.set("map",json.dumps(dict))