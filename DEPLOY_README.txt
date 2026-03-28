【公开仓库部署说明（三容器源码构建版）】

一、适用场景
1) 代码已公开在 Git 仓库
2) 对方机器可从源码构建镜像（无需你手工发安装包）
3) 数据库使用官方 mysql:8.0
4) 对方无需你手工传数据库文件（仓库内 SQL 自动导入）

二、对方机器前置条件
1) 已安装 Docker Desktop
2) 已安装 Git
3) 能访问 GitHub 和 Docker Hub

三、首次部署（对方执行）
1) git clone <你的公开仓库地址>
2) cd <仓库目录>
3) deploy.cmd
5) 浏览器访问：http://localhost

说明：deploy.cmd 会自动 `docker compose down -v` 后 `docker compose up -d --build`，并从源码构建三个容器。

说明：MySQL 首次启动时会自动执行 docker/mysql/init 下 SQL（包含 003_back_end_data.sql 与 004_add_indexes.sql），把 back_end 数据导入并补齐性能索引。

四、版本升级（对方执行）
1) git pull
2) deploy.cmd

五、发布新版本（你执行）
1) 在仓库提交代码并推送到 GitHub
2) 对方机器执行 `git pull` 后执行 `deploy.cmd`

（可选）你仍可保留 GitHub Actions 构建发布流程，但部署本身不依赖 Docker Hub。

六、常见问题
1) 端口占用
- 修改 docker-compose.yml 中 80/3307 映射端口

2) 数据未刷新或需全量重导
- docker compose down -v
- docker compose up -d

3) 容器检查
- docker compose ps
- docker compose logs mysql
- docker compose logs backend
- docker compose logs frontend

4) 依赖下载慢或失败（构建 backend 时）
- 通常是 Maven/PyPI 网络问题，不是项目逻辑问题。
- 可重试：docker compose build --no-cache backend
- 或配置代理/镜像源后再执行 deploy.cmd

七、你本机“清空后重建并发布”
1) 在仓库根目录执行：rebuild_and_publish.cmd
