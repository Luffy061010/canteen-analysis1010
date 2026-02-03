#!/usr/bin/env python3
"""
Apply seed user: ensure user row for student 202401010101 exists and set password to 123456.
This script reads DB config from `canteen-analysis-python/config/mysql.py` and updates/inserts into `user` table.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'canteen-analysis-python')))

try:
    from config import mysql
except Exception as e:
    print('Failed to import DB config:', e)
    sys.exit(1)

import pymysql

USERNAME = '202401010101'
PASSWORD = '123456'

sql_check = "SELECT id FROM `user` WHERE username=%s"
sql_update = "UPDATE `user` SET password_hash=SHA2(%s,256), is_admin=0, is_active=1 WHERE username=%s"
sql_insert = "INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) VALUES (%s, SHA2(%s,256), 0, 1, NOW())"

def main():
    cfg = getattr(mysql, 'DBCONFIG', None)
    if not cfg:
        print('DBCONFIG not found in config.mysql')
        sys.exit(1)

    try:
        conn = pymysql.connect(**cfg)
    except Exception as e:
        print('Failed to connect to MySQL:', e)
        sys.exit(1)

    try:
        cur = conn.cursor()
        cur.execute(sql_check, (USERNAME,))
        row = cur.fetchone()
        if row:
            print(f'User {USERNAME} exists (id={row[0]}), updating password...')
            cur.execute(sql_update, (PASSWORD, USERNAME))
            conn.commit()
            print('Password updated to 123456')
        else:
            print(f'User {USERNAME} not found, inserting new user...')
            cur.execute(sql_insert, (USERNAME, PASSWORD))
            conn.commit()
            print('User inserted with password 123456')
        cur.close()
    except Exception as e:
        print('SQL execution error:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
