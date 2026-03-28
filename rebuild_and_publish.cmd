@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set VERSION=V1.0.0

echo [1/6] 清理本地旧容器和卷
docker compose down -v

echo [2/6] 构建并推送前端/backend 镜像
call release.cmd
if errorlevel 1 exit /b 1

echo [3/6] 导出最新 back_end 数据库 SQL
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\export-back_end-dump.ps1" -HostName 127.0.0.1 -Port 3306 -User root -Password 123456 -Database back_end
if errorlevel 1 (
  echo [WARN] 导出 SQL 失败，请检查本机 MySQL 后重试。
)

echo [4/6] 启动三容器（源码本地构建）
docker compose up -d --build
if errorlevel 1 exit /b 1

echo [5/6] 状态检查
docker compose ps

echo [6/6] 发布完成
echo.
echo 完成：版本 %VERSION%
echo 本机访问: http://localhost
echo 对方部署: git clone 后执行 deploy.cmd
exit /b 0
