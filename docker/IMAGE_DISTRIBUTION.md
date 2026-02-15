# 镜像离线分发清单（docker save/load）

适用于你当前三容器方案：

- `canteen-frontend`
- `canteen-backend`
- `mysql:8.0`

## A. 发送方（你）执行

在项目根目录：

```powershell
# 1) 先导出数据库 SQL（确保别人导入的是你最新数据）
./scripts/export-back_end-dump.ps1 -HostName 127.0.0.1 -Port 3306 -User root -Password 123456 -Database back_end

# 2) 构建三容器所需镜像
docker compose build

# 3) 查看 compose 生成的镜像名（通常是 目录名_服务名）
docker image ls | findstr "frontend backend"

# 4) 打包镜像（按你本机实际名字替换 canteen-frontend / canteen-backend）
docker save -o canteen-images.tar canteen-frontend canteen-backend mysql:8.0

# 5) （可选）压缩以减小体积
tar -czf canteen-images.tar.gz canteen-images.tar
```

把以下内容一起发给对方：

- `canteen-images.tar`（或 `canteen-images.tar.gz`）
- 整个项目目录（至少包含 `docker-compose.yml`、`docker/`、`scripts/`）

## B. 接收方执行

在项目根目录：

```powershell
# 如果收到的是 tar.gz，先解压
tar -xzf canteen-images.tar.gz

# 1) 导入镜像
docker load -i canteen-images.tar

# 2) 启动系统
docker compose up -d
```

访问地址：

- 前端：`http://localhost`

## C. 首次导入数据库说明

- MySQL 只会在 **数据卷为空** 时执行 `docker/mysql/init/*.sql`。
- 如果对方要重新导入你给的新 SQL：

```powershell
docker compose down -v
docker compose up -d
```

## D. 一键重标记（可选）

若 `docker compose up` 提示找不到镜像名，可先重标记：

```powershell
# 查看刚导入的镜像实际名称
docker image ls

# 示例：把导入后的名字重标记为 compose 需要的名字
docker tag <导入后的前端镜像ID或名字> canteen-frontend
docker tag <导入后的后端镜像ID或名字> canteen-backend
```
