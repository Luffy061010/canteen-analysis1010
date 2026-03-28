# 离线部署手册（给普通用户）

本手册用于在**无外网/无法访问 Docker Hub**的机器上部署系统。

## 一、你这边（发布方）做什么

1. 在有网机器打开项目根目录。
2. 双击运行 `make_offline_bundle.cmd`。
3. 等待脚本完成，会生成：

- 文件夹：`offline-bundle-v1.0.0`
- 压缩包：`offline-bundle-v1.0.0.zip`

把 `offline-bundle-v1.0.0.zip` 发给对方（U盘/局域网/网盘都可以）。

## 二、对方机器做什么（离线）

1. 安装并启动 Docker Desktop。
2. 解压 `offline-bundle-v1.0.0.zip`。
3. 双击 `双击我部署.cmd`（或直接运行 `deploy_offline.cmd`）。
4. 看到成功提示后，浏览器打开 `http://localhost`。

## 三、常见问题（普通人处理）

1. 提示找不到 Docker

- 先安装 Docker Desktop。
- 安装后重启电脑再试。

1. 提示 Docker 没启动

- 打开 Docker Desktop，等左下角显示 Running。

1. 网页打不开

- 先等 30~60 秒再刷新。
- 仍不行时，在该目录打开终端执行：
- `docker compose ps`
- `docker compose logs -f`

1. 想重新部署（清空旧数据）

- 重新执行 `deploy_offline.cmd` 即可，脚本会自动清理旧容器和旧数据卷。

## 四、默认端口

- 前端：`http://localhost`
- MySQL 对宿主机：`3307`

如果端口冲突，请联系发布方修改 `docker-compose.yml` 后重新打包。
