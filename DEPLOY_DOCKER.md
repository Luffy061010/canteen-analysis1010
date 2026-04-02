# Docker 异机部署（纯 CMD）

目标：全流程只用 CMD；同事只要拉代码并执行命令，不需要你每次单独发 SQL 文件。

## 1. 构建并推送镜像到 Docker Hub（你执行）

在仓库根目录打开 cmd：

```cmd
publish-images.cmd 你的DockerHub用户名 V1.0
```

这一步会完成：

- `docker login`
- `docker compose build frontend java-backend python-backend`
- `docker compose push frontend java-backend python-backend`

## 2. 同事在自己的机器部署（只用 CMD）

同事拿到代码后，在仓库根目录执行：

```cmd
deploy.cmd 你的DockerHub用户名 V1.0
```

这一步会完成：

- 拉取镜像
- 启动 mysql、redis、python、java、frontend

## 3. 不再单独发 SQL 文件的做法（推荐）

把真实数据 SQL 放在仓库 `models\scripts\back_end_*.sql` 后，同事可直接执行：

```cmd
deploy.cmd 你的DockerHub用户名 V1.0 back_end AUTO
```

该命令会批量导入：`models\scripts\back_end_*.sql`。

## 4. 导入自定义 SQL（可选）

```cmd
docker\mysql\import-database.cmd back_end_alice models\scripts\003_seed_data.sql
```

也可以替换为自己的 SQL 路径，例如：

```cmd
docker\mysql\import-database.cmd back_end_alice backup\my_data.sql
```

## 5. 导入后重启后端（让后端使用新库）

```cmd
docker compose up -d --force-recreate python-backend java-backend
```

## 6. 常用 CMD 运维命令

查看状态：

```cmd
docker compose ps
```

查看日志：

```cmd
docker compose logs -f
```

停止服务：

```cmd
docker compose down
```

清空数据并重建（慎用）：

```cmd
docker compose down -v
docker compose up -d --build
```

## 7. 一条命令部署并导入（可选）

`deploy.cmd` 支持直接带数据库名和 SQL 文件，或 `AUTO` 批量导入：

```cmd
deploy.cmd 你的DockerHub用户名 V1.0 back_end_alice models\scripts\003_seed_data.sql
deploy.cmd 你的DockerHub用户名 V1.0 back_end AUTO
```
