【公开仓库部署说明（四容器固定版）】

一、适用场景
1) 代码已公开在 Git 仓库
2) 镜像已推送到 Docker Hub：
	- lln1010/1010-frontend:v1.0.0
	- lln1010/1010-python:v1.0.0
	- lln1010/1010-java:v1.0.0
3) 数据库使用官方 mysql:8.0
4) 对方无需你手工传数据库文件（仓库内 SQL 自动导入）

二、对方机器前置条件
1) 已安装 Docker Desktop
2) 已安装 Git
3) 能访问 GitHub 和 Docker Hub

三、首次部署（对方执行）
1) git clone <你的公开仓库地址>
2) cd <仓库目录>
3) docker compose pull
4) docker compose up -d
5) 浏览器访问：http://localhost

说明：MySQL 首次启动时会自动执行 docker/mysql/init 下 SQL（包含 003_back_end_data.sql），把 back_end 数据导入到对方机器。

四、版本升级（对方执行）
1) git pull
2) docker compose pull
3) docker compose up -d

五、发布新版本（你执行）
1) 在仓库根目录执行：release.cmd
2) 完成后推送代码：git add . && git commit -m "release: v1.0.0" && git push

六、常见问题
1) 端口占用
- 修改 docker-compose.yml 中 80/3307 映射端口

2) 数据未刷新或需全量重导
- docker compose down -v
- docker compose up -d

3) 容器检查
- docker compose ps
- docker compose logs mysql
- docker compose logs java
- docker compose logs python
- docker compose logs frontend

七、你本机“清空后重建并发布”
1) 在仓库根目录执行：rebuild_and_publish.cmd
