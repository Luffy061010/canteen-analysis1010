import sys
try:
    import pymysql
except Exception:
    print('pymysql 未安装，尝试安装...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymysql'])
    import pymysql

cfg = dict(host='localhost', user='root', password='123456', database='back_end', charset='utf8mb4')
conn = pymysql.connect(**cfg)
cur = conn.cursor()
import re
files = ['models/seed_admin.sql','models/sample_logs.sql']

# --- 自动生成用户并加入 seed ---
def fetch_student_ids(cursor):
    # 尝试从常见表/列中获取学号/学生 id 列表
    candidate_queries = [
        "SELECT student_id FROM student",
        "SELECT student_id FROM students",
        "SELECT id FROM student",
        "SELECT id FROM students",
        "SELECT DISTINCT student_id FROM consumption",
        "SELECT DISTINCT student_id FROM consumptions",
        "SELECT DISTINCT student_id FROM scores",
        "SELECT DISTINCT uid FROM consumption",
        "SELECT DISTINCT uid FROM consumptions",
    ]
    ids = []
    for q in candidate_queries:
        try:
            cursor.execute(q)
            rows = cursor.fetchall()
            if rows:
                # flatten and stringify
                ids = [str(r[0]) for r in rows if r[0] is not None]
                if ids:
                    return ids
        except Exception:
            continue
    return ids


def write_seed_users(ids, out_path='models/seed_users.sql'):
    if not ids:
        return False
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('-- 自动生成的用户种子 SQL\n')
        f.write('-- 密码策略：默认使用学号作为初始密码，数据库使用 SHA2(...,256) 进行哈希\n\n')
        for sid in ids:
            stmt = ("INSERT INTO `user` (username, password_hash, is_admin, is_active, created_at) "
                    f"VALUES ('{sid}', SHA2('{sid}', 256), 0, 1, NOW());\n")
            f.write(stmt)
    return True


# 尝试获取学生 id 列表
student_ids = fetch_student_ids(cur)
if student_ids:
    print(f'检测到 {len(student_ids)} 个学生 id，将生成对应用户。')
    written = write_seed_users(student_ids)
    if written:
        # 将生成的文件加入执行列表（放在后面以保证 admin 先入库）
        files.append('models/seed_users.sql')
else:
    print('未检测到学生表或学生 id 列，跳过自动生成用户。')

for path in files:
    print('执行', path)
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    sql = re.sub(r'--.*?\n', '\n', sql)
    parts = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in parts:
        try:
            cur.execute(stmt)
        except Exception as ex:
            print('执行语句失败:', ex)
            print('语句前200字符:', stmt[:200])
conn.commit()
print('已提交。现在查询示例数据：')
try:
    cur.execute("SELECT id,username,is_admin,is_active,created_at FROM user LIMIT 10")
    users = cur.fetchall()
    print('USERS:', users)
except Exception as e:
    print('查询 user 失败:', e)
try:
    cur.execute("SELECT id,user_id,username,action,detail,created_at FROM log ORDER BY created_at DESC LIMIT 10")
    logs = cur.fetchall()
    print('LOGS:', logs)
except Exception as e:
    print('查询 log 失败:', e)
conn.close()
