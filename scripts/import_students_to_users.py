"""
从学生表或 CSV 批量创建 `user` 表账号。

用法（从数据库表）：
  python scripts/import_students_to_users.py --db-host localhost --db-user root --db-pass 123456 --db-name back_end --table students --id-column student_id

用法（从 CSV）：
  python scripts/import_students_to_users.py --csv models/students.csv --id-column student_id

密码策略：默认使用学号作为密码（可通过 --password-mode 修改为 random 或 fixed:<pwd>）。
"""
import argparse
import csv
import pymysql
import hashlib
import random
import string


def sha256_hash(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()


def generate_random_password(n=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(n))


def insert_user(conn, username, raw_password):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM user WHERE username=%s', (username,))
    if cursor.fetchone():
        return False
    pwd_hash = sha256_hash(raw_password)
    cursor.execute('INSERT INTO user (username, password_hash, is_admin, is_active, created_at) VALUES (%s, %s, %s, %s, NOW())', (username, pwd_hash, 0, 1))
    conn.commit()
    return True


def import_from_db(args):
    conn = pymysql.connect(host=args.db_host, user=args.db_user, password=args.db_pass, database=args.db_name, charset='utf8mb4')
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(f'SELECT {args.id_column} FROM {args.table}')
    rows = cursor.fetchall()
    created = 0
    for r in rows:
        sid = str(r[args.id_column])
        pwd = sid if args.password_mode == 'username' else (generate_random_password() if args.password_mode == 'random' else args.password_mode.split(':',1)[1])
        if insert_user(conn, sid, pwd):
            created += 1
    conn.close()
    print(f'imported {created} users')


def import_from_csv(args):
    with open(args.csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        ids = []
        for row in reader:
            if args.id_column in row and row[args.id_column].strip():
                ids.append(row[args.id_column].strip())
            else:
                # fallback first column
                ids.append(next(iter(row.values())).strip())

    conn = pymysql.connect(host=args.db_host, user=args.db_user, password=args.db_pass, database=args.db_name, charset='utf8mb4')
    created = 0
    for sid in ids:
        pwd = sid if args.password_mode == 'username' else (generate_random_password() if args.password_mode == 'random' else args.password_mode.split(':',1)[1])
        if insert_user(conn, sid, pwd):
            created += 1
    conn.close()
    print(f'imported {created} users from csv')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', help='学生 CSV 路径')
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-user', default='root')
    parser.add_argument('--db-pass', default='123456')
    parser.add_argument('--db-name', default='back_end')
    parser.add_argument('--table', default='students')
    parser.add_argument('--id-column', default='student_id')
    parser.add_argument('--password-mode', default='username', help='username|random|fixed:<pwd>')
    args = parser.parse_args()

    if args.csv:
        import_from_csv(args)
    else:
        import_from_db(args)


if __name__ == '__main__':
    main()
