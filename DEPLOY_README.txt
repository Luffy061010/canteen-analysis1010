【系统部署最终说明（Windows）】

一、最终架构
1) frontend 容器
2) backend 容器（Java + FastAPI）
3) mysql 容器（mysql:8.0）

二、数据库包要不要单独构建
1) 在线源码部署：不需要单独构建数据库包。
2) 原因：数据库容器直接用官方 mysql:8.0，业务库结构和数据通过 docker/mysql/init/*.sql 自动导入。
3) 离线部署：需要把 mysql:8.0 镜像一起打进离线包（make_offline_bundle.cmd 已自动处理）。

三、客户在线部署步骤（推荐）
1) 安装 Docker Desktop 和 Git。
2) 执行：
	git clone <你的仓库地址>
	cd <仓库目录>
	deploy.cmd
3) 访问：http://localhost

四、你发布新版本步骤
1) 本机构建并推送业务镜像（版本固定 V1.0.0）：
	release.cmd
2) 提交代码并推送到 GitHub。
3) 通知客户执行：
	git pull
	deploy.cmd

五、离线部署（客户无法联网时）
1) 你执行：make_offline_bundle.cmd
2) 发送：offline-bundle-V1.0.0.zip
3) 客户解压后执行：deploy_offline.cmd

六、数据库重置和重新导入
1) 执行：
	docker compose down -v
	deploy.cmd

七、故障排查
1) 查看状态：docker compose ps
2) 查看后端日志：docker compose logs backend
3) 查看数据库日志：docker compose logs mysql
4) 查看前端日志：docker compose logs frontend
