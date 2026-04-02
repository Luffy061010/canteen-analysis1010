# Docker 异机部署（软著可用，纯 CMD）

目标：部署方仅使用 CMD 命令完成环境准备、代码获取、镜像拉取与容器启动。

## 1. 运行环境要求

- Windows 10/11（64 位）
- 已联网，可访问 GitHub 与 Docker Hub
- 需安装 Docker Desktop 与 Git

## 2. 安装 Docker Desktop

在 CMD 执行：

```cmd
winget install -e --id Docker.DockerDesktop
```

安装后启动 Docker Desktop，确保 Docker 服务已就绪。

## 3. 安装 Git

在 CMD 执行：

```cmd
winget install -e --id Git.Git
```

## 4. 安装结果校验

在 CMD 执行：

```cmd
docker --version
docker compose version
git --version
```

## 5. 获取系统源码

在 CMD 执行：

```cmd
git clone https://github.com/Luffy061010/canteen-analysis1010.git
cd canteen-analysis1010
```

## 6. 容器化部署（推荐命令）

在项目根目录执行：

```cmd
deploy.cmd 你的DockerHub用户名 V1.0 back_end AUTO
```

说明：

- 该命令会自动拉取 Docker Hub 镜像并启动系统容器。
- 自动初始化/导入 `models\scripts\back_end_*.sql` 数据文件。
- 自动重建后端容器，确保新库配置生效。

> 不建议仅使用 `docker compose pull` + `docker compose up -d` 作为标准流程。
> 原因是镜像命名空间与标签若未显式传入，可能拉取失败或拉取到错误镜像。

## 7. 部署完成校验

在 CMD 执行：

```cmd
docker compose ps
```

当 `mysql`、`redis`、`python-backend`、`java-backend`、`frontend` 均为 `Up` 时，判定部署成功。

## 8. 系统访问

部署成功后可访问：

- 前端：`http://localhost`
- Java API：`http://localhost:8080`
- Python API：`http://localhost:8000`

## 9. 系统更新

当代码或镜像更新后，在项目目录执行：

```cmd
git pull
deploy.cmd 你的DockerHub用户名 V1.0
```

若切换新镜像版本（例如 `V1.1`），执行：

```cmd
deploy.cmd 你的DockerHub用户名 V1.1
```

## 10. 数据重置与重建（可选）

如需清空持久化数据并重建：

```cmd
docker compose down -v
deploy.cmd 你的DockerHub用户名 V1.0 back_end AUTO
```

注意：该操作会删除已持久化数据，请确认后执行。

## 11. 常用运维命令

```cmd
docker compose logs -f
docker compose down
```
