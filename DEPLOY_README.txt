【公开仓库部署说明（推荐）】

一、适用场景
1) 代码已公开在 Git 仓库
2) 镜像已推送到 Docker Hub（lln1010/1010-frontend、lln1010/1010-backend、lln1010/1010-mysql）
3) 对方无需你手工传文件，直接 git clone 即可

二、对方机器前置条件
1) 已安装 Docker Desktop
2) 已安装 Git
3) 能访问 GitHub 和 Docker Hub

三、首次部署（对方执行）
1) git clone <你的公开仓库地址>
2) cd <仓库目录>
3) （可选）创建 .env 指定版本标签，例如：
	FRONTEND_TAG=v1.0.1
	BACKEND_TAG=v1.0.1
	MYSQL_TAG=8.0
4) 双击 deploy.cmd（或执行 docker compose pull ; docker compose up -d）
5) 浏览器访问：http://localhost

四、版本升级（对方执行）
1) git pull
2) docker compose pull
3) docker compose up -d

五、发布新版本（你执行）
1) 构建并推送新镜像（建议不要只用 latest，使用 vX.Y.Z 标签）
2) 更新仓库中的文档或 .env.example（告知新标签）
3) git push

六、常见问题
1) 端口占用
- 修改 docker-compose.yml 中 80/3307 映射端口

2) 数据未刷新
- 首次全量重置：docker compose down -v
- 再执行：docker compose up -d

3) 容器检查
- docker compose ps
- docker compose logs mysql
- docker compose logs backend
- docker compose logs frontend
