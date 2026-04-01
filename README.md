# 校园食堂消费分析系统（五容器部署）

本项目支持使用 Docker Compose 以五个容器部署：

- 前端：Nginx + Vue 构建产物
- Python 后端：FastAPI
- Java 后端：Spring Boot
- MySQL 数据库
- Redis 缓存

## 目录

- `canteen-analysis/`：Java 后端
- `canteen-analysis-python/`：Python 后端
- `canteen-analysis-system10.10.6/vite-project/`：前端
- `models/scripts/`：数据库初始化与数据导入 SQL（首次建库时自动执行）

## 推荐部署策略（抗网络抖动）

为了尽可能避免因网络抖动导致部署失败，建议固定采用两阶段流程：

1. 发布机（网络较稳定）先构建并推送版本镜像。
2. 部署机只做拉取与启动；若拉取失败，自动回退到本地缓存镜像。

这样部署机不依赖每次都在线构建，成功率更高、速度也更稳定。

## 阶段 A：发布镜像（建议在稳定网络环境执行）

1. 登录 Docker Hub：

```bash
docker login
```

1. 执行发布脚本（已内置重试）：

```bat
publish-images.cmd 你的DockerHub用户名 V1.0
```

脚本会自动重试构建和推送，推送以下镜像：

- `你的DockerHub用户名/canteen-frontend:V1.0`
- `你的DockerHub用户名/canteen-python-backend:V1.0`
- `你的DockerHub用户名/canteen-java-backend:V1.0`
- `你的DockerHub用户名/canteen-mysql:V1.0`

Redis 使用官方镜像 `redis:7.2-alpine`。

## 阶段 B：部署上线（Windows 一键）

1. 复制环境变量模板并修改命名空间与版本（仅首次需要）：

cmd 终端执行：

copy /Y .env.example .env

`.env` 里至少确认这两项：

- `DOCKERHUB_NAMESPACE=你的DockerHub用户名`
- `IMAGE_TAG=V1.0`

1. 启动部署：

```bat
deploy.cmd
```

`deploy.cmd` 为纯 cmd 实现，默认流程为：

1. 自动重试检查 Docker。
2. `docker compose pull` 失败时自动重试。
3. 若镜像拉取失败但本地有缓存镜像，则继续启动。
4. 若镜像缺失，则自动回退到本地构建（可重试）。
5. 启动后自动执行 MySQL/Redis 健康检查，以及前后端 HTTP 可用性检查。

## deploy.cmd 常用参数

- 重建数据库（会清空 MySQL 卷并重新导入 `models/scripts`）：

```bat
deploy.cmd -ResetData
```

- 完全离线部署（不拉取，仅使用本地镜像/本地构建）：

```bat
deploy.cmd -SkipPull
```

- 提高重试强度（弱网环境推荐）：

```bat
deploy.cmd -RetryCount 6 -RetryDelaySec 10
```

## 兜底说明（真正的一劳永逸）

建议每次版本发布后，将关键镜像导出归档一份，跨环境传输时可离线导入：

```bash
docker save yourname/canteen-frontend:V1.0 -o canteen-frontend_V1.0.tar
docker save yourname/canteen-python-backend:V1.0 -o canteen-python-backend_V1.0.tar
docker save yourname/canteen-java-backend:V1.0 -o canteen-java-backend_V1.0.tar
docker save yourname/canteen-mysql:V1.0 -o canteen-mysql_V1.0.tar
```

部署机离线导入：

```bash
docker load -i canteen-frontend_V1.0.tar
docker load -i canteen-python-backend_V1.0.tar
docker load -i canteen-java-backend_V1.0.tar
docker load -i canteen-mysql_V1.0.tar
```

导入后执行：

```bat
deploy.cmd -SkipPull
```

## 本地开发/调试常用命令

在仓库根目录执行：

```bash
docker compose up -d --build
docker compose ps
```

停止并删除容器：

```bash
docker compose down
```

## 本地构建前置（仅在镜像缺失时）

当部署脚本无法拉取镜像且本地也没有缓存时，会回退到 `docker compose build`。

Java 服务镜像依赖本地 JAR，请确保存在：

`canteen-analysis/target/canteen-analysis-0.0.1-SNAPSHOT.jar`

若不存在，先执行：

```bash
cd canteen-analysis
mvn -DskipTests clean package
```

## 数据导入约定

你可以将业务数据导入 SQL 放在 `models/scripts/003_seed_data.sql`（或其他按序号命名的 `.sql` 文件）中，容器首次初始化会自动导入。

如果你希望自动导出当前正在运行的真实业务库到该文件（该导出脚本是 PowerShell，仅用于数据导出，不影响部署与推送全 cmd）：

```powershell
powershell -ExecutionPolicy Bypass -File .\export-real-data.ps1 -ContainerName mysql -Database back_end -RootPassword 123456
```

导出完成后，重建数据库验证导入：

```bash
docker compose down -v
docker compose up -d --build
```

默认账号：

- 用户名：`lin`
- 密码：`061010`
