"""
创建初始管理员账号到 MySQL `user` 表。

用法:
  python scripts/seed_admin.py --host localhost --user root --password 123456 --database back_end --username admin --password admin123

如果管理员用户名已存在，脚本会提示并退出。
"""
import argparse
import pymysql
import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=3306)
    parser.add_argument('--user', default='root')
    parser.add_argument('--password', default='123456')
    parser.add_argument('--database', default='back_end')
    parser.add_argument('--username', default='admin')
    parser.add_argument('--password-admin', dest='admin_password', default='admin123')
    args = parser.parse_args()

    conn = pymysql.connect(host=args.host, port=args.port, user=args.user, password=args.password, database=args.database, charset='utf8mb4')
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM user WHERE username=%s', (args.username,))
    if cursor.fetchone():
        print(f"用户名 {args.username} 已存在，跳过创建")
        conn.close()
        return

    pwd_hash = hash_password(args.admin_password)
    cursor.execute('INSERT INTO user (username, password_hash, is_admin, is_active, created_at) VALUES (%s, %s, %s, %s, NOW())',
                   (args.username, pwd_hash, 1, 1))
    conn.commit()
    print(f"已创建管理员用户 {args.username}")
    conn.close()


if __name__ == '__main__':
    main()
