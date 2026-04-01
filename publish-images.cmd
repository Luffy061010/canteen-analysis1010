@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

set DOCKERHUB_NAMESPACE=%~1
if "%DOCKERHUB_NAMESPACE%"=="" (
    echo 用法: publish-images.cmd ^<dockerhub_namespace^> [image_tag]
    echo 例如: publish-images.cmd yourname V1.0
    exit /b 1
)

set IMAGE_TAG=%~2
if "%IMAGE_TAG%"=="" set IMAGE_TAG=V1.0

set RETRY_MAX=4
set RETRY_DELAY=8

if not "%~3"=="" set RETRY_MAX=%~3
if not "%~4"=="" set RETRY_DELAY=%~4

echo [1/4] Check Docker login state
for /f "delims=" %%i in ('docker info --format "{{.RegistryConfig.IndexConfigs}}" 2^>nul') do set _REG=%%i
if "%_REG%"=="" (
    echo [WARN] 无法确认登录状态，请先执行 docker login
)

echo [2/4] Prefetch base layers ^(best effort^)
set DOCKERHUB_NAMESPACE=%DOCKERHUB_NAMESPACE%
set IMAGE_TAG=%IMAGE_TAG%
docker compose pull >nul 2>&1

echo [3/4] Build images with retry
call :run_with_retry "docker compose build --pull" "docker compose build"
if errorlevel 1 goto :fail

echo [4/4] Push images with retry
call :run_with_retry "docker compose push" "docker compose push"
if errorlevel 1 goto :fail

echo [DONE] Done
echo 已推送镜像：
echo   %DOCKERHUB_NAMESPACE%/canteen-frontend:%IMAGE_TAG%
echo   %DOCKERHUB_NAMESPACE%/canteen-python-backend:%IMAGE_TAG%
echo   %DOCKERHUB_NAMESPACE%/canteen-java-backend:%IMAGE_TAG%
echo   %DOCKERHUB_NAMESPACE%/canteen-mysql:%IMAGE_TAG%
exit /b 0

:fail
echo 发布失败，请检查上面的错误信息。
exit /b 1

:run_with_retry
set "RUN_CMD=%~1"
set "STEP_NAME=%~2"
set /a ATTEMPT=1

:retry_loop
echo [RETRY] !STEP_NAME! attempt !ATTEMPT!/%RETRY_MAX%
call !RUN_CMD!
if not errorlevel 1 exit /b 0

if !ATTEMPT! GEQ %RETRY_MAX% (
    echo [ERROR] !STEP_NAME! reached max retry count.
    exit /b 1
)

set /a WAIT_SEC=%RETRY_DELAY%*ATTEMPT
echo [WARN] !STEP_NAME! failed, retry after !WAIT_SEC! seconds...
timeout /t !WAIT_SEC! /nobreak >nul
set /a ATTEMPT+=1
goto :retry_loop
