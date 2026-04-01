"""
FastAPI 后端入口：用户与权限、日志、数据分析相关接口。
"""
import json
import csv
import io
import os
import time
import logging
from typing import Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, Query, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymysql
import hashlib
import jwt

from service import analysis_service
from schemas.form_dto import ClusterBody, CorrelationBody, DriftBody, BaseBody
from utils import get_data_summary
from utils import redis_utils as r
from config import mysql
import math
import numpy as np
from utils.llm_explainer import build_custom_explanation


app = FastAPI()
logger = logging.getLogger(__name__)


class ExplainBody(BaseModel):
    scene: Optional[str] = None
    style: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    prompt: Optional[str] = None

# 用户模型
class User(BaseModel):
    id: int = None
    username: str
    password_hash: str = None
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime = None

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False
    is_active: bool = True

class UserLogin(BaseModel):
    username: str
    password: str

# 数据库连接配置（优先使用 config.mysql 中的 DBCONFIG）
DB_CONFIG = getattr(mysql, 'DBCONFIG', None) or {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'back_end',
    'charset': 'utf8mb4'
}

# JWT 配置（请使用更安全的 SECRET_KEY）
SECRET_KEY = 'your_jwt_secret_key'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # 检查黑名单
        if r.get_key(f"bl:{token}"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已登出")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        is_admin = payload.get("is_admin")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效")
        return {"username": username, "user_id": user_id, "is_admin": is_admin}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token校验失败")

def admin_required(current_user=Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user


def normalize_pagination(page: int, page_size: int, default_size: int = 20, max_size: int = 500):
    safe_page = max(1, int(page or 1))
    safe_size = int(page_size or default_size)
    safe_size = max(1, min(safe_size, max_size))
    return safe_page, safe_size

# 获取用户列表（仅管理员） 支持分页
@app.get('/users')
def get_users(
    page: int = 1,
    page_size: int = Query(20, alias='page_size'),
    username: Optional[str] = None,
    is_admin: Optional[bool] = None,
    current_user=Depends(admin_required)
):
    page, page_size = normalize_pagination(page, page_size, default_size=20, max_size=200)
    offset = (page - 1) * page_size
    where_clauses = []
    params = []
    if username:
        where_clauses.append('username LIKE %s')
        params.append(f'%{username}%')
    if is_admin is not None:
        where_clauses.append('is_admin=%s')
        params.append(1 if is_admin else 0)

    where_sql = (' WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT id, username, is_admin, is_active, created_at FROM user{where_sql} ORDER BY id LIMIT %s OFFSET %s',
        tuple(params + [page_size, offset])
    )
    users = cursor.fetchall()
    cursor.execute(f'SELECT COUNT(*) FROM user{where_sql}', tuple(params))
    total = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": u[0],
                "username": u[1],
                "is_admin": bool(u[2]),
                "is_active": bool(u[3]),
                "created_at": u[4].strftime('%Y-%m-%d %H:%M:%S') if u[4] else None
            } for u in users
        ]
    }

# 添加用户（仅管理员）
@app.post('/users')
def add_user(user: UserCreate, current_user=Depends(admin_required)):
    username = str(user.username or '').strip()
    password = user.password or ''
    if not username:
        raise HTTPException(status_code=400, detail='用户名不能为空')
    if len(password) < 6:
        raise HTTPException(status_code=400, detail='密码至少 6 位')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM user WHERE username=%s', (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail='用户名已存在')
    password_hash = hash_password(password)
    cursor.execute(
        'INSERT INTO user (username, password_hash, is_admin, is_active) VALUES (%s, %s, %s, %s)',
        (username, password_hash, bool(user.is_admin), bool(user.is_active))
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    write_log(current_user["user_id"], current_user["username"], 'add_user', f'添加用户 {username}')
    return {'msg': '添加成功', 'id': user_id}

# 删除用户（仅管理员）
@app.delete('/users/{user_id}')
def delete_user(user_id: int, current_user=Depends(admin_required)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM user WHERE id=%s', (user_id,))
    user_row = cursor.fetchone()
    cursor.execute('DELETE FROM user WHERE id=%s', (user_id,))
    conn.commit()
    conn.close()
    uname = user_row[0] if user_row else str(user_id)
    write_log(current_user["user_id"], current_user["username"], 'delete_user', f'删除用户 {uname}')
    return {'msg': '删除成功'}

# 修改用户状态（禁用/启用，仅管理员）
@app.put('/users/{user_id}/status')
def update_user_status(user_id: int, is_active: bool, current_user=Depends(admin_required)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE user SET is_active=%s WHERE id=%s', (is_active, user_id))
    cursor.execute('SELECT username FROM user WHERE id=%s', (user_id,))
    user_row = cursor.fetchone()
    conn.commit()
    uname = user_row[0] if user_row else str(user_id)
    write_log(current_user["user_id"], current_user["username"], 'update_user_status', f'修改用户 {uname} 状态为 {is_active}')
    conn.close()
    return {'msg': '状态更新成功'}

# 用户查个人信息
@app.get('/me')
def get_me(current_user=Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, is_admin, is_active, created_at FROM user WHERE id=%s', (current_user["user_id"],))
    u = cursor.fetchone()
    conn.close()
    if not u:
        raise HTTPException(status_code=404, detail='用户不存在')
    return {
        "id": u[0],
        "username": u[1],
        "is_admin": bool(u[2]),
        "is_active": bool(u[3]),
        "created_at": u[4].strftime('%Y-%m-%d %H:%M:%S') if u[4] else None
    }


# 修改密码（用户本人）
class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str


class ForgotPasswordBody(BaseModel):
    username: str
    new_password: str

@app.post('/change-password')
def change_password(body: ChangePasswordBody, current_user=Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM user WHERE id=%s', (current_user['user_id'],))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='用户不存在')
    if hash_password(body.old_password) != row[0]:
        conn.close()
        raise HTTPException(status_code=400, detail='旧密码错误')
    new_hash = hash_password(body.new_password)
    cursor.execute('UPDATE user SET password_hash=%s WHERE id=%s', (new_hash, current_user['user_id']))
    conn.commit()
    conn.close()
    write_log(current_user['user_id'], current_user['username'], 'change_password', '修改密码')
    return {'msg': '密码修改成功'}


@app.post('/forgot-password')
def forgot_password(body: ForgotPasswordBody):
    username = str(body.username or '').strip()
    new_password = body.new_password or ''
    if not username:
        raise HTTPException(status_code=400, detail='用户名不能为空')
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail='新密码至少 6 位')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, is_active FROM user WHERE username=%s', (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='用户不存在')

    user_id = row[0]
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE user SET password_hash=%s WHERE id=%s', (new_hash, user_id))
    conn.commit()
    conn.close()
    write_log(user_id, username, 'forgot_password', '通过忘记密码重置密码')
    return {'msg': '密码重置成功'}


# 注销（登出）: 将当前 token 加入黑名单
@app.post('/logout')
def logout(token: str = Depends(oauth2_scheme), current_user=Depends(get_current_user)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get('exp')
        if exp:
            ttl = int(exp - datetime.utcnow().timestamp())
            if ttl < 0:
                ttl = 0
        else:
            ttl = 3600
    except Exception:
        ttl = 3600
    # 存 Redis 黑名单
    try:
        r.r.set(f'bl:{token}', '1', ex=ttl)
    except Exception:
        r.set_key(f'bl:{token}', '1')
    write_log(current_user['user_id'], current_user['username'], 'logout', '用户登出')
    return {'msg': '已登出'}


# 管理员修改用户角色（设为/取消 管理员）
@app.put('/users/{user_id}/role')
def set_user_role(user_id: int, is_admin: bool, current_user=Depends(admin_required)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE user SET is_admin=%s WHERE id=%s', (is_admin, user_id))
    conn.commit()
    cursor.execute('SELECT username FROM user WHERE id=%s', (user_id,))
    row = cursor.fetchone()
    conn.close()
    uname = row[0] if row else str(user_id)
    write_log(current_user['user_id'], current_user['username'], 'set_role', f'设置用户 {uname} is_admin={is_admin}')
    return {'msg': '角色更新成功'}
# 日志记录函数
def write_log(user_id: int, username: str, action: str, detail: str = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO log (user_id, username, action, detail) VALUES (%s, %s, %s, %s)',
        (user_id, username, action, detail)
    )
    conn.commit()
    conn.close()


def ensure_admin_requests_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_requests (
      id BIGINT PRIMARY KEY AUTO_INCREMENT,
      user_id BIGINT NOT NULL,
      username VARCHAR(128) NOT NULL,
      reason TEXT,
      status VARCHAR(32) DEFAULT 'pending',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      processed_by BIGINT,
      processed_at TIMESTAMP NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    conn.close()


def ensure_performance_indexes():
    index_specs = [
        ("consumption_data_students_consumption", "idx_consumption_student_time", "student_id, consumption_time", False),
        ("consumption_data_students_consumption", "idx_consumption_time", "consumption_time", False),
        ("basic_data_student", "idx_student_college", "college", False),
        ("basic_data_student", "idx_student_major", "major", False),
        ("basic_data_student", "idx_student_grade", "grade", False),
        ("basic_data_student", "idx_student_class", "class_name", False),
        ("basic_data_student", "idx_student_id", "student_id", True),
    ]

    conn = get_db()
    cursor = conn.cursor()
    try:
        for table_name, index_name, columns, is_unique in index_specs:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = %s
                LIMIT 1
                """,
                (table_name,)
            )
            if not cursor.fetchone():
                continue

            cursor.execute(
                """
                SELECT 1
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                  AND index_name = %s
                LIMIT 1
                """,
                (table_name, index_name)
            )
            if cursor.fetchone():
                continue

            create_sql = f"CREATE {'UNIQUE ' if is_unique else ''}INDEX {index_name} ON {table_name} ({columns})"
            cursor.execute(create_sql)

        conn.commit()
    finally:
        conn.close()


@app.post('/admin/apply')
def apply_admin(reason: Optional[str] = Body(None, embed=True), current_user=Depends(get_current_user)):
    # 普通登录用户提交管理员申请
    ensure_admin_requests_table()
    conn = get_db()
    cursor = conn.cursor()
    # 如果已经是管理员，不必提交
    if current_user.get('is_admin'):
        conn.close()
        raise HTTPException(status_code=400, detail='已经是管理员')
    # 检查是否已有未处理申请
    cursor.execute('SELECT id FROM admin_requests WHERE user_id=%s AND status=%s', (current_user['user_id'], 'pending'))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail='已有未处理的管理员申请')
    cursor.execute('INSERT INTO admin_requests (user_id, username, reason, status) VALUES (%s, %s, %s, %s)',
                   (current_user['user_id'], current_user['username'], reason or '', 'pending'))
    conn.commit()
    conn.close()
    write_log(current_user['user_id'], current_user['username'], 'admin_apply', '申请管理员')
    return {'msg': '管理员申请已提交'}


@app.get('/admin/applications')
def list_admin_applications(page: int = 1, page_size: int = 20, current_user=Depends(admin_required)):
    ensure_admin_requests_table()
    page, page_size = normalize_pagination(page, page_size, default_size=20, max_size=200)
    offset = (page - 1) * page_size
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, reason, status, created_at, processed_by, processed_at FROM admin_requests ORDER BY created_at DESC LIMIT %s OFFSET %s', (page_size, offset))
    rows = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) FROM admin_requests')
    total = cursor.fetchone()[0]
    conn.close()
    items = []
    for r in rows:
        items.append({
            'id': r[0], 'user_id': r[1], 'username': r[2], 'reason': r[3], 'status': r[4], 'created_at': r[5].strftime('%Y-%m-%d %H:%M:%S') if r[5] else None,
            'processed_by': r[6], 'processed_at': r[7].strftime('%Y-%m-%d %H:%M:%S') if r[7] else None
        })
    return {'total': total, 'page': page, 'page_size': page_size, 'items': items}


@app.put('/admin/applications/{app_id}/approve')
def approve_admin_application(app_id: int, current_user=Depends(admin_required)):
    ensure_admin_requests_table()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, status FROM admin_requests WHERE id=%s', (app_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='申请不存在')
    user_id, status = row
    if status != 'pending':
        conn.close()
        raise HTTPException(status_code=400, detail='申请已处理')
    # 更新用户为管理员
    cursor.execute('UPDATE user SET is_admin=1 WHERE id=%s', (user_id,))
    cursor.execute('UPDATE admin_requests SET status=%s, processed_by=%s, processed_at=NOW() WHERE id=%s', ('approved', current_user['user_id'], app_id))
    conn.commit()
    conn.close()
    write_log(current_user['user_id'], current_user['username'], 'admin_approve', f'批准申请 {app_id} -> user {user_id}')
    return {'msg': '已批准'}

# 日志查询接口（支持分页）
@app.get('/logs')
def get_logs(page: int = 1, page_size: int = 50, current_user=Depends(get_current_user), user_id: int = None):
    page, page_size = normalize_pagination(page, page_size, default_size=50, max_size=500)
    offset = (page - 1) * page_size
    conn = get_db()
    cursor = conn.cursor()
    if current_user["is_admin"] and not user_id:
        cursor.execute('SELECT id, user_id, username, action, detail, created_at FROM log ORDER BY created_at DESC LIMIT %s OFFSET %s', (page_size, offset))
        logs = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM log')
        total = cursor.fetchone()[0]
    else:
        uid = user_id if (user_id and current_user["is_admin"]) else current_user["user_id"]
        cursor.execute('SELECT id, user_id, username, action, detail, created_at FROM log WHERE user_id=%s ORDER BY created_at DESC LIMIT %s OFFSET %s', (uid, page_size, offset))
        logs = cursor.fetchall()
        cursor.execute('SELECT COUNT(*) FROM log WHERE user_id=%s', (uid,))
        total = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": l[0],
                "user_id": l[1],
                "username": l[2],
                "action": l[3],
                "detail": l[4],
                "created_at": l[5].strftime('%Y-%m-%d %H:%M:%S') if l[5] else None
            } for l in logs
        ]
    }


# 导出日志 CSV（仅管理员）
@app.get('/logs/export')
def export_logs(
        username: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        current_user=Depends(admin_required)
):
    where_clauses = []
    params = []
    if username:
        where_clauses.append('username LIKE %s')
        params.append(f'%{username}%')
    if action:
        where_clauses.append('action LIKE %s')
        params.append(f'%{action}%')
    if start_date:
        where_clauses.append('created_at >= %s')
        params.append(start_date)
    if end_date:
        where_clauses.append('created_at <= %s')
        params.append(end_date)

    where_sql = ' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f'SELECT id, user_id, username, action, detail, created_at FROM log{where_sql} ORDER BY created_at DESC', params)
    rows = cursor.fetchall()
    conn.close()

    def excel_text(val, force_text=False):
        if val is None:
            return ''
        text = str(val)
        if force_text or (text.isdigit() and len(text) >= 11):
            return f'="{text}"'
        return text

    def gen():
        yield '\ufeff'
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'user_id', 'username', 'action', 'detail', 'created_at'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for r in rows:
            created = r[5].strftime('%Y-%m-%d %H:%M:%S') if r[5] else ''
            detail = (r[4] or '').replace('\n', ' ').replace('\r', ' ')
            writer.writerow([
                excel_text(r[0]),
                excel_text(r[1]),
                excel_text(r[2], force_text=True),
                r[3] or '',
                detail,
                excel_text(created, force_text=True)
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    headers = {
        'Content-Disposition': f'attachment; filename=logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    }
    return StreamingResponse(gen(), media_type='text/csv; charset=utf-8', headers=headers)


# 日志搜索（支持按用户名、操作类型、日期范围过滤）
@app.get('/logs/search')
def search_logs(username: Optional[str] = None, action: Optional[str] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None,
                page: int = 1, page_size: int = 50, current_user=Depends(get_current_user)):
    page, page_size = normalize_pagination(page, page_size, default_size=50, max_size=500)
    offset = (page - 1) * page_size
    where_clauses = []
    params = []
    if username:
        where_clauses.append('username LIKE %s')
        params.append(f'%{username}%')
    if action:
        where_clauses.append('action LIKE %s')
        params.append(f'%{action}%')
    if start_date:
        where_clauses.append('created_at >= %s')
        params.append(start_date)
    if end_date:
        where_clauses.append('created_at <= %s')
        params.append(end_date)

    base = 'SELECT id, user_id, username, action, detail, created_at FROM log'
    count_base = 'SELECT COUNT(*) FROM log'
    if where_clauses:
        where_sql = ' WHERE ' + ' AND '.join(where_clauses)
    else:
        where_sql = ''

    conn = get_db()
    cursor = conn.cursor()
    # 管理员可以查看所有，普通用户只能查看自己的日志
    if not current_user['is_admin']:
        if where_sql:
            where_sql += ' AND user_id=%s'
        else:
            where_sql = ' WHERE user_id=%s'
        params.append(current_user['user_id'])

    cursor.execute(f"{base}{where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [page_size, offset])
    rows = cursor.fetchall()
    cursor.execute(f"{count_base}{where_sql}", params)
    total = cursor.fetchone()[0]
    conn.close()

    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'items': [
            {
                'id': r[0], 'user_id': r[1], 'username': r[2], 'action': r[3], 'detail': r[4],
                'created_at': r[5].strftime('%Y-%m-%d %H:%M:%S') if r[5] else None
            } for r in rows
        ]
    }


# 删除日志（仅管理员）
class LogDeleteBody(BaseModel):
    logIds: list[int]

@app.delete('/logs')
def delete_logs(body: LogDeleteBody, current_user=Depends(admin_required)):
    ids = body.logIds
    if not ids:
        raise HTTPException(status_code=400, detail='logIds 不能为空')
    placeholders = ','.join(['%s'] * len(ids))
    sql = f'DELETE FROM log WHERE id IN ({placeholders})'
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, tuple(ids))
    conn.commit()
    conn.close()
    write_log(current_user['user_id'], current_user['username'], 'delete_logs', f'deleted {len(ids)} logs')
    return {'msg': '删除成功', 'deleted': len(ids)}

def get_db():
    cfg = dict(DB_CONFIG)
    cfg.setdefault('connect_timeout', 5)
    cfg.setdefault('read_timeout', 30)
    cfg.setdefault('write_timeout', 30)
    conn = pymysql.connect(**cfg)
    return conn


def wait_for_db_ready(max_retries: int = 60, interval_seconds: int = 2):
    last_error = None
    for i in range(1, max_retries + 1):
        try:
            conn = get_db()
            conn.close()
            logger.info("[startup] mysql is ready (attempt %s/%s)", i, max_retries)
            return
        except Exception as e:
            last_error = e
            logger.warning("[startup] waiting mysql (%s/%s): %s", i, max_retries, e)
            time.sleep(interval_seconds)
    raise RuntimeError(f"mysql not ready after retries: {last_error}")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def ensure_default_admin_account():
    conn = get_db()
    cursor = conn.cursor()
    default_hash = hash_password('061010')
    cursor.execute(
        """
        INSERT INTO user (username, password_hash, is_admin, is_active)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            password_hash = VALUES(password_hash),
            is_admin = VALUES(is_admin),
            is_active = VALUES(is_active)
        """,
        ('lin', default_hash, True, True)
    )
    conn.commit()
    conn.close()


@app.on_event('startup')
def bootstrap_security_defaults():
    try:
        wait_for_db_ready(max_retries=90, interval_seconds=2)
        ensure_default_admin_account()
        ensure_admin_requests_table()
        ensure_performance_indexes()
    except Exception as e:
        # 不阻断服务启动，避免因数据库就绪时序导致整个容器退出
        logger.warning("[startup] bootstrap security defaults skipped: %s", e)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 注册接口
@app.post('/register')
def register(user: UserCreate):
    username = str(user.username or '').strip()
    password = user.password or ''
    # 强制账号为学号（全数字），并且要在 basic_data_student 表中存在
    if not username or not username.isdigit():
        raise HTTPException(status_code=400, detail='用户名必须为学号（仅数字）')
    if len(password) < 6:
        raise HTTPException(status_code=400, detail='密码至少 6 位')

    conn = get_db()
    cursor = conn.cursor()
    # 检查学号是否在学生基础表中存在（允许缺失，避免阻断新生注册）
    student_exists = None
    try:
        cursor.execute('SELECT student_id FROM basic_data_student WHERE student_id=%s', (username,))
        student_exists = cursor.fetchone() is not None
    except Exception:
        # 如果 basic_data_student 表不存在或查询失败，允许继续注册
        student_exists = None

    cursor.execute('SELECT id FROM user WHERE username=%s', (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail='用户名已存在')

    password_hash = hash_password(password)
    cursor.execute('INSERT INTO user (username, password_hash) VALUES (%s, %s)', (username, password_hash))
    conn.commit()
    user_id = cursor.lastrowid
    if student_exists is False:
        try:
            cursor.execute(
                'INSERT INTO basic_data_student (student_id, name) VALUES (%s, %s)',
                (username, username)
            )
            conn.commit()
        except Exception:
            # 基础表字段约束不同，插入失败时忽略，让注册继续完成
            pass
    conn.close()
    if student_exists is False:
        write_log(user_id, username, 'register', '用户注册（学号未登记到学生信息表）')
    else:
        write_log(user_id, username, 'register', '用户注册')
    # 自动为新注册用户签发 token 并返回用户信息，便于前端登录后直接使用
    token = create_access_token({"sub": username, "user_id": user_id, "is_admin": False})
    user_obj = {"id": user_id, "username": username, "is_admin": False, "is_active": True}
    return {"token": token, "token_type": "bearer", "user": user_obj}

# 登录接口
@app.post('/login')
def login(user: UserLogin):
    username = str(user.username or '').strip()
    password = user.password or ''
    if not username or not password:
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, is_admin, is_active FROM user WHERE username=%s', (username,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    user_id, password_hash, is_admin, is_active = result
    if hash_password(password) != password_hash:
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    if not is_active:
        raise HTTPException(status_code=403, detail='账号已禁用')
    token = create_access_token({"sub": username, "user_id": user_id, "is_admin": is_admin})
    write_log(user_id, username, 'login', '用户登录')
    user_obj = {"id": user_id, "username": username, "is_admin": bool(is_admin), "is_active": bool(is_active)}
    # 兼容老客户端字段并提供更方便的 'token'/'user' 返回格式
    return {"access_token": token, "token_type": "bearer", "token": token, "user": user_obj}

# 添加CORS配置解决跨域问题
cors_env = os.getenv("CORS_ALLOW_ORIGINS", "")
cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] if cors_env else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/analysis/cluster")
def analysis_cluster(cluster_body: ClusterBody = Depends()):
    logger.debug("analysis_cluster request: %s", cluster_body)
    # 版本号防止旧缓存（字段不全）命中
    key = "api:cluster:v7:" + cluster_body.model_dump_json()
    val = r.get_key(key)
    if val:
        return json.loads(val)

    res = analysis_service.analysis_cluster(cluster_body)
    r.set_key(key, json.dumps(res))
    return res


@app.get("/analysis/cluster/details")
def analysis_cluster_details(
    studentIds: str = Query(..., description="学号列表，逗号分隔"),
    timeBegin: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    timeEnd: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    includeLlm: bool = Query(False, description="是否生成个体解释")
):
    ids = [i.strip() for i in str(studentIds or "").split(",") if i and i.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="studentIds 不能为空")

    begin_date = None
    end_date = None
    normalized_begin = timeBegin or "2024-09-01"
    normalized_end = timeEnd or "2024-09-30"
    try:
        begin_date = datetime.strptime(normalized_begin, "%Y-%m-%d").date()
        end_date = datetime.strptime(normalized_end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="timeBegin/timeEnd 日期格式错误，需 YYYY-MM-DD")

    ids_for_cache = sorted(set(ids))
    ids_raw = ",".join(ids_for_cache)
    ids_digest = hashlib.md5(ids_raw.encode("utf-8")).hexdigest()
    cache_key = f"api:cluster:details:v4:{ids_digest}:{normalized_begin}:{normalized_end}:{int(includeLlm)}"
    val = r.get_key(cache_key)
    if val:
        return json.loads(val)

    details = analysis_service.get_cluster_details(ids, begin_date, end_date, includeLlm)
    res = {"results": details, "total": len(details)}
    r.set_key(cache_key, json.dumps(res), ex=300)
    return res


@app.get("/analysis/drift")
def analysis_drift(drift_body: DriftBody = Depends()):
    logger.debug("analysis_drift request: %s", drift_body)
    # 版本号防止旧缓存命中（窗口推进逻辑变更）
    key = "api:drift:v7:" + drift_body.model_dump_json()
    val = r.get_key(key)
    if val:
        return json.loads(val)

    res = analysis_service.analysis_drift(drift_body)
    r.set_key(key, json.dumps(res))
    return res


@app.get("/analysis/correlation")
def analysis_correlation(correlation_body: CorrelationBody = Depends()):
    logger.debug("analysis_correlation request: %s", correlation_body)
    key = "api:correlation:v6:" + correlation_body.model_dump_json()
    val = r.get_key(key)
    if val:
        return json.loads(val)

    res = analysis_service.analysis_correlation(correlation_body)
    r.set_key(key, json.dumps(res))
    return res


@app.get("/analysis/dashboard/overview")
def dashboard_overview(base_body: BaseBody = Depends()):
    key = "api:dashboard:overview:v1:" + base_body.model_dump_json()
    val = r.get_key(key)
    if val:
        return json.loads(val)

    try:
        res = analysis_service.get_dashboard_overview(base_body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"dashboard overview failed: {e}")

    r.set_key(key, json.dumps(res), ex=180)
    return res


@app.post("/analysis/explain")
@app.post("/analysis/llm/explain")
@app.post("/analysis/deepseek/explain")
def analysis_explain(body: ExplainBody = Body(...)):
    user_prompt = (body.prompt or "").strip()
    scene = (body.scene or "通用场景").strip()
    style = (body.style or "plain-chinese").strip()
    data = body.data or {}

    if not user_prompt:
        raise HTTPException(status_code=400, detail="prompt 不能为空")

    full_prompt = (
        f"场景: {scene}。"
        f"输出风格: {style}。"
        "请严格基于给定结构化数据解释，不要臆造。"
        f"\n数据: {json.dumps(data, ensure_ascii=False)}"
        f"\n任务: {user_prompt}"
    )

    text = build_custom_explanation(full_prompt)
    if text:
        return {"text": text, "scene": scene}

    # LLM 不可用时按场景降级，避免不同分析场景混用错误话术。
    if scene == "group-portrait":
        groups = data.get("groups", []) if isinstance(data, dict) else []

        def _fmt_group(g):
            level = g.get("level", "-")
            ratio = g.get("ratio", 0)
            avg_daily = g.get("avgDailyAvg", 0)
            avg_count = g.get("avgDailyCount", 0)
            sample_size = g.get("sampleSize", 0)
            return (
                f"{level}群体样本{sample_size}人，占比约{ratio}%，"
                f"日均消费约{avg_daily}元、日均消费次数约{avg_count}次。"
            )

        text_parts = []
        if isinstance(groups, list) and groups:
            ordered = ["低消费", "较低消费", "中消费", "高消费"]
            group_map = {str(i.get("level", "")): i for i in groups if isinstance(i, dict)}
            for lv in ordered:
                item = group_map.get(lv, {"level": lv, "sampleSize": 0, "ratio": 0, "avgDailyAvg": 0, "avgDailyCount": 0})
                text_parts.append(_fmt_group(item))

        if not text_parts:
            text_parts = [
                "低消费群体通常预算约束更明显，消费频次与单次金额整体较低。",
                "较低消费群体消费节奏较为稳定，以基础就餐需求为主。",
                "中消费群体在成本与体验之间保持平衡，结构相对均衡。",
                "高消费群体更重视时效与偏好，单次消费与波动性通常更高。",
            ]

        fallback = (
            "四类消费层级群体解释如下："
            + "".join(text_parts)
            + "上述结论仅反映群体消费行为特征，不代表任何行政认定。"
        )
    elif scene == "score-correlation":
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        top_rows = data.get("topRows", []) if isinstance(data, dict) else []

        sample_size = summary.get("sampleSize", 0)
        significant_count = summary.get("significantCount", 0)
        main_direction = summary.get("mainDirection", "方向待定")
        main_strength = summary.get("mainStrength", "弱")

        if isinstance(top_rows, list) and top_rows:
            top = top_rows[0] if isinstance(top_rows[0], dict) else {}
            top_feature = top.get("feature", "关键指标")
            top_corr = top.get("corr", "0.000")
            top_p = top.get("pValue", "1.0000")
            top_direction = top.get("direction", "相关方向待定")

            second = top_rows[1] if len(top_rows) > 1 and isinstance(top_rows[1], dict) else {}
            third = top_rows[2] if len(top_rows) > 2 and isinstance(top_rows[2], dict) else {}
            extra_parts = []
            if second:
                extra_parts.append(
                    f"其次是{second.get('feature', '次级指标')}（{second.get('direction', '方向待定')}，r={second.get('corr', '0.000')}）。"
                )
            if third:
                extra_parts.append(
                    f"第三是{third.get('feature', '第三指标')}（{third.get('direction', '方向待定')}，r={third.get('corr', '0.000')}）。"
                )

            fallback = (
                f"【概览】本次分析样本量约为{sample_size}，显著相关指标{significant_count}项，整体呈现{main_direction}，强度为{main_strength}。"
                f"【重点指标】当前最值得关注的是{top_feature}（{top_direction}，r={top_corr}，p={top_p}）。"
                + "".join(extra_parts)
                + "【业务解读】可将其理解为同一群体内指标的同步变化倾向，而非单个行为对成绩的直接作用。"
                + "【风险与边界】该结论可能受到课程难度、考试周期、出勤、作息及样本窗口长度等因素影响。"
                + "【建议动作】建议在同一筛选口径下持续观察4-8周；将消费、考勤、课程负担做联动分析；"
                + "针对高波动人群开展分层支持并复盘干预前后变化。"
                + "该结果仅反映统计相关关系，不代表因果关系。"
            )
        else:
            fallback = (
                "当前筛选范围内可用于关联分析的有效样本不足。"
                "建议优先扩大时间区间、放宽筛选条件，或先在学院/年级层面观察总体趋势后再下钻到班级与个人。"
                "该结果仅反映统计相关关系，不代表因果关系。"
            )
    elif scene == "score-correlation-personal":
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        profile = data.get("studentProfile", {}) if isinstance(data, dict) else {}
        sid = profile.get("studentId", "-")
        daily = profile.get("dailyAvg", 0)
        monthly = profile.get("monthlyAvg", 0)
        gpa = profile.get("gpa", 0)
        avg_daily = summary.get("avgDaily", 0)
        avg_gpa = summary.get("avgGpa", 0)
        try:
            diff_daily = float(daily) - float(avg_daily)
        except Exception:
            diff_daily = 0.0
        try:
            diff_gpa = float(gpa) - float(avg_gpa)
        except Exception:
            diff_gpa = 0.0
        daily_flag = "高于" if diff_daily >= 0 else "低于"
        gpa_flag = "高于" if diff_gpa >= 0 else "低于"
        fallback = (
            f"【个人概况】学号{sid}在当前筛选范围内，日均消费约{daily}元、月均消费约{monthly}元，GPA约{gpa}。"
            f"【群体对比】与同口径群体均值比较，日均消费{daily_flag}群体约{abs(diff_daily):.2f}元，"
            f"GPA{gpa_flag}群体约{abs(diff_gpa):.2f}。"
            "【位置解读】该学生在“消费-成绩”坐标中与群体中心存在偏移，适合结合周度波动持续观察而非一次性定性。"
            "【风险与边界】短期事件（考试周、活动、兼职、节假日）可能放大偏差，需要联合考勤与作息信息判读。"
            "【建议动作】建议连续观察4-8周消费波动与绩点变化，识别异常日期并记录事件原因；"
            "同时结合课程负担与出勤做交叉验证，必要时提供个性化预算与学习节律建议。"
            "该结果仅反映统计相关关系，不代表因果关系。"
        )
    else:
        portrait = data.get("portrait", {}) if isinstance(data, dict) else {}
        metrics = data.get("metrics", {}) if isinstance(data, dict) else {}
        level = portrait.get("level", "当前层级")
        activity = portrait.get("activity", "常规活跃度")
        schedule = portrait.get("schedule", "日常分布")
        month_amount = metrics.get("monthAvgAmount", "-")
        month_count = metrics.get("monthAvgCount", "-")
        daily_amount = metrics.get("dailyAvg", "-")
        daily_count = metrics.get("dailyCount", "-")
        peak_period = metrics.get("peakPeriod", "-")
        favorite_window = metrics.get("favoriteWindow", "常去窗口")
        fallback = (
            f"当前画像显示你属于{level}，整体活跃度为{activity}，消费节奏呈现{schedule}。"
            f"从指标看，日均消费约{daily_amount}元、日均消费次数约{daily_count}次，"
            f"月均消费约{month_amount}元、月均消费次数约{month_count}次，"
            f"消费高峰多出现在{peak_period}，常去窗口为{favorite_window}。"
            "整体说明你的消费习惯具有一定稳定性。建议优先保持规律餐次与预算边界，"
            "对高峰时段的单次消费做简单记录，连续观察2-4周后再调整。"
            "以上结论仅反映消费行为特征，不代表任何行政认定。"
        )
    return {"text": fallback, "scene": scene, "fallback": True}


# 🔥 修改的接口：使用查询参数而不是请求体
@app.get("/analysis/summary/data")
def get_summary_data(
        college: Optional[str] = Query(None, description="学院"),
        start_date: Optional[str] = Query(None, description="开始日期"),
        end_date: Optional[str] = Query(None, description="结束日期")
):
    """
    接受查询参数而不是请求体
    """
    logger.debug("summary params: college=%s start_date=%s end_date=%s", college, start_date, end_date)

    # 处理日期转换
    start_date_parsed = None
    end_date_parsed = None

    if start_date:
        try:
            start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "开始日期格式错误，请使用 YYYY-MM-DD 格式"}

    if end_date:
        try:
            end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "结束日期格式错误，请使用 YYYY-MM-DD 格式"}

    # 创建 BaseBody 对象
    try:
        base_body = BaseBody(
            college=college,
            start_date=start_date_parsed,
            end_date=end_date_parsed
        )
    except Exception as e:
        logger.exception("创建BaseBody错误")
        return {"error": f"参数处理失败: {str(e)}"}

    # 继续原有逻辑
    key = "api:summary:" + base_body.model_dump_json()
    val = r.get_key(key)
    if val:
        return json.loads(val)

    try:
        df = get_data_summary.get_data_summary(base_body)
        df.reset_index(inplace=True)
        df = df.rename(columns={'index': 'student_id'})

        r.set_key(key, json.dumps(df.to_dict(orient="records")))
        return df.to_dict(orient="records")
    except Exception as e:
        logger.exception("数据处理错误")
        return {"error": f"数据处理失败: {str(e)}"}


@app.get("/")
def hello():
    return {"message": "校园消费分析系统 API 服务运行正常"}


@app.get('/consumption/query')
def consumption_query(
        studentId: Optional[str] = Query(None, description='学号'),
        start_date: Optional[str] = Query(None, description='开始日期 YYYY-MM-DD'),
        end_date: Optional[str] = Query(None, description='结束日期 YYYY-MM-DD'),
        include_raw: bool = Query(False, description='是否包含原始消费记录'),
        page: int = Query(1, description='页码'),
        page_size: int = Query(100, description='每页大小')
):
    if not studentId:
        raise HTTPException(status_code=400, detail='需要指定 studentId')

    # 解析日期
    sd = None
    ed = None
    try:
        if start_date:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
    except Exception:
        raise HTTPException(status_code=400, detail='日期格式错误，需 YYYY-MM-DD')

    # 构建 BaseBody 调用已有汇总函数
    from schemas.form_dto import BaseBody
    bb = BaseBody(studentId=studentId, timeBegin=sd, timeEnd=ed)
    try:
        summary_df = get_data_summary.get_data_summary(bb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'获取汇总失败: {e}')

    summary = {}
    sid = studentId
    if sid in summary_df.index:
        row = summary_df.loc[sid]
        summary = {
            'studentId': sid,
            'breakfast_avg_count': float(row.get('breakfast_avg_count', 0.0)),
            'breakfast_avg_amount': float(row.get('breakfast_avg_amount', 0.0)),
            'lunch_avg_count': float(row.get('lunch_avg_count', 0.0)),
            'lunch_avg_amount': float(row.get('lunch_avg_amount', 0.0)),
            'dinner_avg_count': float(row.get('dinner_avg_count', 0.0)),
            'dinner_avg_amount': float(row.get('dinner_avg_amount', 0.0))
        }
    else:
        summary = {"msg": "无汇总数据"}

    result = {'summary': summary}

    # 默认返回原始记录（方便个人查看）；如果前端明确不需要可以传 include_raw=false
    if include_raw is None:
        include_raw = True

    if include_raw:
        page, page_size = normalize_pagination(page, page_size, default_size=100, max_size=1000)
        conn = pymysql.connect(**mysql.DBCONFIG)
        try:
            cur = conn.cursor()
            where = 'WHERE student_id=%s'
            params = [studentId]
            if sd and ed:
                where += ' AND consumption_time BETWEEN %s AND %s'
                params.extend([sd, ed])

            # count
            cur.execute(f"SELECT COUNT(*) FROM consumption_data_students_consumption {where}", tuple(params))
            total = cur.fetchone()[0]

            offset = (page - 1) * page_size
            cur.execute(
                f"SELECT id, student_id, consumption_time, amount, meal_type FROM consumption_data_students_consumption {where} ORDER BY consumption_time DESC LIMIT %s OFFSET %s",
                tuple(params + [page_size, offset])
            )
            rows = cur.fetchall()

            raw_records = [
                {"id": r[0], "studentId": r[1], "consumption_time": r[2].isoformat() if hasattr(r[2], 'isoformat') else str(r[2]), "amount": float(r[3]), "meal_type": r[4]} for r in rows
            ]
            result['raw'] = {'total': int(total), 'page': page, 'page_size': page_size, 'items': raw_records}

            # 额外返回近期趋势（过去 14 天的日消费序列）以供个人页面展示
            try:
                today = datetime.utcnow().date()
                window_days = 14
                start_recent = today - timedelta(days=window_days - 1)
                cur.execute(
                    "SELECT DATE(consumption_time) d, SUM(amount) t FROM consumption_data_students_consumption WHERE student_id=%s AND consumption_time BETWEEN %s AND %s GROUP BY DATE(consumption_time) ORDER BY d",
                    (studentId, start_recent, today)
                )
                rows2 = cur.fetchall()
                recent_map = {r[0].isoformat(): float(r[1]) for r in rows2}
                dates = [(start_recent + timedelta(days=i)).isoformat() for i in range(window_days)]
                series = [round(recent_map.get(d, 0.0), 2) for d in dates]
                # 移动平均（窗口3）
                ma = []
                w = 3
                for i in range(len(series)):
                    seg = series[max(0, i - w + 1):i + 1]
                    ma.append(round(sum(seg) / len(seg), 2) if seg else 0.0)

                result['recent'] = {'dates': dates, 'series': series, 'moving_average': ma}
            except Exception:
                pass
            finally:
                cur.close()
        finally:
            conn.close()

    return result


@app.get('/consumption/{studentId}/recent')
def consumption_recent(studentId: str, days: int = Query(14, description='最近多少天')):
    if days <= 0:
        raise HTTPException(status_code=400, detail='days 必须大于 0')

    today = datetime.utcnow().date()
    current_start = today - timedelta(days=days - 1)
    previous_start = current_start - timedelta(days=days)
    previous_end = current_start - timedelta(days=1)

    conn = pymysql.connect(**mysql.DBCONFIG)
    cur = conn.cursor()
    # 查询 previous + current 两个区间的日汇总
    cur.execute(
        """
        SELECT DATE(consumption_time) as d, SUM(amount) as total
        FROM consumption_data_students_consumption
        WHERE student_id=%s AND consumption_time BETWEEN %s AND %s
        GROUP BY DATE(consumption_time)
        ORDER BY d
        """,
        (studentId, previous_start, today)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # 构建字典
    totals = {r[0].isoformat(): float(r[1]) for r in rows}

    dates_current = [(current_start + timedelta(days=i)).isoformat() for i in range(days)]
    current_series = [totals.get(d, 0.0) for d in dates_current]

    dates_previous = [(previous_start + timedelta(days=i)).isoformat() for i in range(days)]
    previous_series = [totals.get(d, 0.0) for d in dates_previous]

    total_current = sum(current_series)
    total_previous = sum(previous_series)
    if math.isclose(total_previous, 0.0):
        change_rate = None
    else:
        change_rate = round((total_current - total_previous) / total_previous * 100.0, 2)

    # 额外分析：移动平均、线性趋势斜率、平均每日消费、峰值日期
    try:
        arr_x = np.arange(len(current_series))
        arr_y = np.array(current_series, dtype=float)
        if len(arr_x) >= 2 and np.any(arr_y):
            # 线性拟合 slope
            m, b = np.polyfit(arr_x, arr_y, 1)
            slope = float(m)
        else:
            slope = 0.0
    except Exception:
        slope = 0.0

    # 移动平均（窗口3）
    ma = []
    w = 3
    for i in range(len(current_series)):
        seg = current_series[max(0, i - w + 1):i + 1]
        ma.append(round(sum(seg) / len(seg), 2) if seg else 0.0)

    avg_daily = round(total_current / days, 2) if days > 0 else 0.0
    # 峰值日
    peak_amount = max(current_series) if current_series else 0.0
    peak_date = dates_current[current_series.index(peak_amount)] if peak_amount > 0 and peak_amount in current_series else None

    return {
        'studentId': studentId,
        'days': days,
        'dateRange': {'current_start': current_start.isoformat(), 'current_end': today.isoformat(), 'previous_start': previous_start.isoformat(), 'previous_end': previous_end.isoformat()},
        'total_current': round(total_current, 2),
        'total_previous': round(total_previous, 2),
        'change_rate_percent': change_rate,
        'trend_slope_per_day': round(slope, 4),
        'average_daily': avg_daily,
        'peak_date': peak_date,
        'peak_amount': round(peak_amount, 2),
        'daily': [{'date': d, 'amount': round(a, 2)} for d, a in zip(dates_current, current_series)],
        'moving_average': ma
    }
