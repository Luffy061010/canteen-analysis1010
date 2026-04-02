@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if "%~1"=="" goto :usage

set "DOCKERHUB_NAMESPACE=%~1"
set "IMAGE_TAG=%~2"
if "%IMAGE_TAG%"=="" set "IMAGE_TAG=V1.0"

echo [INFO] Namespace: %DOCKERHUB_NAMESPACE%
echo [INFO] Image tag: %IMAGE_TAG%

echo [INFO] Login Docker Hub...
docker login
if errorlevel 1 (
  echo [ERROR] docker login failed.
  exit /b 1
)

echo [INFO] Build images...
docker compose build frontend java-backend python-backend
if errorlevel 1 (
  echo [ERROR] docker compose build failed.
  exit /b 1
)

echo [INFO] Push images...
docker compose push frontend java-backend python-backend
if errorlevel 1 (
  echo [ERROR] docker compose push failed.
  exit /b 1
)

echo [DONE] Images pushed successfully.
echo [DONE] %DOCKERHUB_NAMESPACE%/canteen-frontend:%IMAGE_TAG%
echo [DONE] %DOCKERHUB_NAMESPACE%/canteen-java:%IMAGE_TAG%
echo [DONE] %DOCKERHUB_NAMESPACE%/canteen-python:%IMAGE_TAG%
exit /b 0

:usage
echo Usage: publish-images.cmd ^<dockerhub_namespace^> [image_tag]
echo Example: publish-images.cmd yourname V1.0
exit /b 1
