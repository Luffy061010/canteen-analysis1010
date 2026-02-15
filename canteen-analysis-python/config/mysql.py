import os

HOST = os.getenv("MYSQL_HOST", "localhost")
PORT = int(os.getenv("MYSQL_PORT", "3306"))
USER = os.getenv("MYSQL_USER", "root")
PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
DATABASE = os.getenv("MYSQL_DATABASE", "back_end")

DBCONFIG = {
    'host': HOST,
    'port': PORT,
    'user': USER,
    'password': PASSWORD,
    'database': DATABASE,
}