# 校园食堂消费分析系统（Windows + Docker 源码部署）

本项目默认使用 3 个容器：

- `frontend`：Vue + Nginx
- `backend`：Java(Spring Boot) + FastAPI（合并在一个容器）
- `mysql`：MySQL 8.0

别人不需要你手工发安装包。只要能访问你的 GitHub 仓库，就可以在自己的 Windows 电脑上从源码构建并部署。

## 1. 目标机器前置条件

- Windows 10/11
- Docker Desktop（已启动）
- Git

## 2. 首次部署（对方机器执行）

```bat
git clone <你的仓库地址>
cd <仓库目录>
deploy.cmd
```

说明：

- `deploy.cmd` 会自动执行 `docker compose down -v` 后再 `docker compose up -d --build`
- 会从源码构建前端和后端镜像
- MySQL 在首次启动（空卷）时自动导入 `docker/mysql/init/*.sql`

访问地址：`http://localhost`

## 3. 数据库初始化与重置

- 首次部署自动导入：
  - `docker/mysql/init/001_init_schema.sql`
  - `docker/mysql/init/002_business_schema_min.sql`
  - `docker/mysql/init/003_back_end_data.sql`
  - `docker/mysql/init/004_add_indexes.sql`
- 需要重置并重新导入：

```bat
docker compose down -v
docker compose up -d --build
```

## 4. 常用命令

- 查看状态：`docker compose ps`
- 查看日志：`docker compose logs -f`
- 后端日志：`docker compose logs -f backend`
- MySQL 日志：`docker compose logs -f mysql`
