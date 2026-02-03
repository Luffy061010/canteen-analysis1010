"""
生成用户种子 SQL 的脚本。

用法示例：
  python scripts/generate_users.py --count 100 --start 100001 --password-mode username
  python scripts/generate_users.py --csv models/students.csv --password-mode username

输出：
  models/seed_users.sql

规则：
- username 将使用学号（student_id）
- password_mode 可选：username（密码等于学号）、random（生成 8 位随机密码）、fixed:<pwd>（固定密码）
- SQL 中使用 MySQL 的 SHA2(...,256) 生成与数据库一致的哈希

"""
import csv
import argparse
import random
import string
from datetime import datetime

TEMPLATE_HEADER = "-- 自动生成的用户种子 SQL\n-- 运行前请确认 `user` 表结构与项目一致\n\n"


def generate_random_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def load_students_from_csv(path):
    students = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 期望列名包含 student_id 或 id
            sid = None
            for k in ('student_id', 'id', '学号', '学号/ID'):
                if k in row and row[k].strip():
                    sid = row[k].strip()
                    break
            if not sid:
                # 尝试第一列
                first = next(iter(row.values()))
                sid = str(first).strip()
            name = row.get('name') or row.get('姓名') or ''
            students.append({'id': sid, 'name': name})
    return students


def build_insert_stmt(username, raw_password, is_admin=0, is_active=1):
    # 使用 MySQL SHA2 函数，保持与现有 seed_admin.sql 格式一致
    now = 'NOW()'
    stmt = ("INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) "
            f"VALUES ('{username}', SHA2('{raw_password}', 256), {is_admin}, {is_active}, {now});")
    return stmt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', help='输入学生 CSV 路径（包含 student_id 列）')
    parser.add_argument('--count', type=int, help='生成的用户数量（用于合成数据）')
    parser.add_argument('--start', type=int, default=100001, help='合成用户起始学号')
    parser.add_argument('--password-mode', default='username', help="密码策略：username|random|fixed:<pwd>")
    parser.add_argument('--out', default='models/seed_users.sql', help='输出 SQL 文件路径')
    args = parser.parse_args()

    students = []
    if args.csv:
        students = load_students_from_csv(args.csv)
        if not students:
            print('未从 CSV 读取到学生数据，请检查文件格式。')
            return
    else:
        if not args.count:
            print('必须提供 --csv 或 --count 来生成用户。')
            return
        # 合成学生id
        for i in range(args.count):
            sid = str(args.start + i)
            students.append({'id': sid, 'name': ''})

    lines = [TEMPLATE_HEADER]
    for s in students:
        username = s['id']
        if args.password_mode == 'username':
            pwd = username
        elif args.password_mode.startswith('fixed:'):
            pwd = args.password_mode.split(':', 1)[1]
        elif args.password_mode == 'random':
            pwd = generate_random_password()
        else:
            pwd = username
        stmt = build_insert_stmt(username, pwd)
        lines.append(stmt + '\n')

    with open(args.out, 'w', encoding='utf-8') as f:
        f.writelines('\n'.join(lines))

    print(f'已写入 {args.out}，共 {len(students)} 条用户记录（明文密码按 SQL 中展示）。')


if __name__ == '__main__':
    main()
