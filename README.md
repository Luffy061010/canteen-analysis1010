# 校园食堂消费分析系统（Docker 部署）

本仓库支持“公开仓库 + Docker Hub 镜像”一键部署：对方无需你手工传文件。

## 1. 对外发布前（你）

1. 将前端/后端镜像推送到 Docker Hub（建议打版本标签）：

- `lln1010/1010-frontend:vX.Y.Z`
- `lln1010/1010-backend:vX.Y.Z`
- `lln1010/1010-mysql:8.0`

1. 更新版本说明（可选）：

- 复制 `.env.example` 为 `.env` 并写入本次版本标签

1. 提交并推送仓库：

- `git add .`
- `git commit -m "release: vX.Y.Z"`
- `git push`

## 2. 首次部署（对方）

1. 克隆仓库：

- `git clone <你的公开仓库地址>`
- `cd <仓库目录>`

1. 可选：固定镜像版本：

- `copy .env.example .env`
- 编辑 `.env` 中 `FRONTEND_TAG`、`BACKEND_TAG`

1. 启动：

- 双击 `deploy.cmd`
- 或执行：`docker compose pull` / `docker compose up -d`

1. 访问：

- `http://localhost`

## 3. 后续升级（对方）

- `git pull`
- `docker compose pull`
- `docker compose up -d`

## 4. 常见问题

- 端口占用：修改 `docker-compose.yml` 的端口映射
- 数据要重置：`docker compose down -v` 后再 `docker compose up -d`
- 容器状态：`docker compose ps`
