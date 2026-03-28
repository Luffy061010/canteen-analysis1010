@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set VERSION=v1.0.0
set BUNDLE_DIR=offline-bundle-%VERSION%
set IMAGE_ARCHIVE=canteen-images-%VERSION%.tar
set ZIP_NAME=%BUNDLE_DIR%.zip

echo [0/8] Preflight checks
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker command not found. Please install Docker Desktop.
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker is not running. Please start Docker Desktop.
  exit /b 1
)

echo [1/8] Prepare bundle directory: %BUNDLE_DIR%
if exist "%BUNDLE_DIR%" rmdir /s /q "%BUNDLE_DIR%"
if exist "%ZIP_NAME%" del /f /q "%ZIP_NAME%"
mkdir "%BUNDLE_DIR%\images"
mkdir "%BUNDLE_DIR%\docker\mysql\init"

echo [2/8] Pull required images
docker pull mysql:8.0 || goto :fail
docker pull lln1010/1010-frontend:%VERSION% || goto :fail
docker pull lln1010/1010-python:%VERSION% || goto :fail
docker pull lln1010/1010-java:%VERSION% || goto :fail

echo [3/8] Save image archive
docker save -o "%BUNDLE_DIR%\images\%IMAGE_ARCHIVE%" mysql:8.0 lln1010/1010-frontend:%VERSION% lln1010/1010-python:%VERSION% lln1010/1010-java:%VERSION% || goto :fail

echo [4/8] Copy compose and SQL init files
copy /Y "docker-compose.yml" "%BUNDLE_DIR%\docker-compose.yml" >nul || goto :fail
copy /Y "deploy_offline.cmd" "%BUNDLE_DIR%\deploy_offline.cmd" >nul || goto :fail
xcopy /E /I /Y "docker\mysql\init" "%BUNDLE_DIR%\docker\mysql\init" >nul || goto :fail

echo [5/8] Create bundle readme
(
  echo Offline deployment bundle - version %VERSION%
  echo.
  echo Usage on target machine:
  echo 1^) Install and start Docker Desktop.
  echo 2^) Unzip this folder.
  echo 3^) Double-click deploy_offline.cmd.
  echo 4^) Open http://localhost
  echo.
  echo If failed, run:
  echo - docker compose ps
  echo - docker compose logs -f
) > "%BUNDLE_DIR%\README_OFFLINE.txt"

echo [6/8] Create helper start script
(
  echo @echo off
  echo cd /d "%%~dp0"
  echo call deploy_offline.cmd
  echo pause
) > "%BUNDLE_DIR%\双击我部署.cmd"

echo [7/8] Compress bundle to zip
powershell -NoProfile -Command "Compress-Archive -Path '%BUNDLE_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force" || goto :fail

echo [8/8] Done
echo Bundle path: %cd%\%BUNDLE_DIR%
echo Image archive: %BUNDLE_DIR%\images\%IMAGE_ARCHIVE%
echo Zip package: %cd%\%ZIP_NAME%
exit /b 0

:fail
echo.
echo Build offline bundle failed.
exit /b 1
