# 校园食堂消费分析系统（Docker 部署）

本项目固定为 4 个容器：

- `frontend`：Vue + Nginx
- `python`：FastAPI
- `java`：Spring Boot
- `mysql`：MySQL 8.0

镜像版本固定为 `v1.0.0`，数据库数据来自仓库内 `docker/mysql/init/003_back_end_data.sql`，首次部署会自动导入。

## 1. 你发布系统（上传到 Docker Hub）

在项目根目录执行：

- `release.cmd`

会构建并推送以下镜像：

- `lln1010/1010-frontend:v1.0.0`
- `lln1010/1010-python:v1.0.0`
- `lln1010/1010-java:v1.0.0`

## 2. 他人命令行部署（无需你额外传数据库文件）

```bash
git clone <你的仓库地址>
cd <仓库目录>
docker compose pull
docker compose up -d
```

访问：`http://localhost`

## 3. 数据库导入说明

- MySQL 在 `docker compose up -d` 的首次初始化（空卷）时，会自动执行 `docker/mysql/init/*.sql`
- 如需重新导入数据：

```bash
docker compose down -v
docker compose up -d
```

## 4. 常用命令

- 查看状态：`docker compose ps`
- 查看日志：`docker compose logs -f`
- 更新版本（同标签重拉）：`docker compose pull && docker compose up -d`
