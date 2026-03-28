@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set VERSION=V1.0.0
set FRONTEND=lln1010/1010-frontend:%VERSION%
set BACKEND=lln1010/1010-backend:%VERSION%

echo [1/6] Docker login
docker login
if errorlevel 1 exit /b 1

echo [2/6] Build frontend image %FRONTEND%
docker build -f docker/frontend/Dockerfile -t %FRONTEND% .
if errorlevel 1 exit /b 1

echo [3/6] Build backend image %BACKEND%
docker build -f docker/backend/Dockerfile.fullstack -t %BACKEND% .
if errorlevel 1 exit /b 1

echo [4/6] Push frontend version tag
docker push %FRONTEND%
if errorlevel 1 exit /b 1

echo [5/6] Push backend version tag
docker push %BACKEND%
if errorlevel 1 exit /b 1

echo [6/6] Release summary
echo.
echo Release done: %VERSION% ^(fixed^)
exit /b 0
