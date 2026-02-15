import os

HOST = os.getenv("REDIS_HOST", "localhost")
PORT = int(os.getenv("REDIS_PORT", "6379"))
PASSWORD = os.getenv("REDIS_PASSWORD", "123112")
DB = os.getenv("REDIS_DB", "0")

REDISCONFIG = {
    'host': HOST,
    'port': PORT,
    'password': PASSWORD,
    'db': DB,
}