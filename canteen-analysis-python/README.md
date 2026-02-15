运行与测试说明

1. 创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. 配置数据库与 Redis：
- 编辑 `c:/Users/32828/Desktop/1010/canteen-analysis-python/main.py` 中 `DB_CONFIG`，填写 `host/user/password/database`。
- 如果使用 Redis，确保 `utils/redis_utils.py` 中 `REDISCONFIG` 正确。

3. 创建表：
- 在数据库中执行 `models/user.sql` 和 `models/log.sql` 创建用户和日志表。

4. 启动服务：

```bash
uvicorn main:app --reload --port 8000
```

5. 常用接口：
- `POST /register` 注册
- `POST /login` 登录，返回 `access_token`
- `POST /forgot-password` 忘记密码重置（按用户名重置）
- `GET /users?page=1&page_size=20` 管理员获取用户列表
- `POST /change-password` 修改密码
- `POST /logout` 注销（登出）
- `GET /logs?page=1&page_size=50` 查询日志
- `GET /logs/export` 导出日志 CSV（管理员）

默认管理员：`lin` / `061010`（由 SQL 初始化脚本与服务启动时自动校准）。

注意：在开发环境请使用安全的 `SECRET_KEY` 并保护数据库凭据。