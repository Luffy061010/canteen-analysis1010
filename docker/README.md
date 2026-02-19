# 四容器 Docker 部署说明

本方案固定为 4 个容器：

- `frontend`：Nginx + Vue 前端
- `java`：Spring Boot
- `python`：FastAPI
- `mysql`：MySQL 8.0

## 1. 导出你本机的 `back_end` 数据库

在项目根目录执行（PowerShell）：

```powershell
./scripts/export-back_end-dump.ps1 -HostName 127.0.0.1 -Port 3306 -User root -Password 123456 -Database back_end
```

导出后会生成/覆盖：

- `docker/mysql/init/003_back_end_data.sql`

这个 SQL 会被别人部署时自动导入。

## 2. 构建并启动

```powershell
docker compose up -d --build
```

访问：

- 前端：`http://localhost`

## 3. 初始化逻辑说明

MySQL 容器首次启动时会自动执行 `docker/mysql/init/*.sql`：

1. `001_init_schema.sql`：基础表和默认管理员
2. `002_business_schema_min.sql`：占位文件（真实业务结构在 003）
3. `003_back_end_data.sql`：你导出的真实业务结构与数据

> 注意：只有在 `mysql_data` 卷为空时才会执行初始化 SQL。

## 4. 重新导入新数据

如果你更新了 `003_back_end_data.sql`，需要重建数据库卷再启动：

```powershell
docker compose down -v
docker compose up -d --build
```

如果仍需手动覆盖导入一次，可执行：

```powershell
docker exec canteen-mysql mysql -uroot -p123456 back_end -e "source /docker-entrypoint-initdb.d/003_back_end_data.sql"
```
