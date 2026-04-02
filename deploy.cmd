@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if "%~1"=="" goto :usage

set "DOCKERHUB_NAMESPACE=%~1"
set "IMAGE_TAG=%~2"
set "MYSQL_DATABASE=%~3"
set "SQL_FILE=%~4"

if "%IMAGE_TAG%"=="" set "IMAGE_TAG=V1.0"
if "%MYSQL_DATABASE%"=="" set "MYSQL_DATABASE=back_end"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=80"
if "%JAVA_PORT%"=="" set "JAVA_PORT=8080"
if "%PYTHON_PORT%"=="" set "PYTHON_PORT=8000"

echo [INFO] Namespace: %DOCKERHUB_NAMESPACE%
echo [INFO] Image tag: %IMAGE_TAG%
echo [INFO] Database : %MYSQL_DATABASE%

if not exist ".env" (
  if exist ".env.example" (
    copy /Y .env.example .env >nul
    echo [INFO] .env created from .env.example
  )
)

echo [INFO] Pull images from Docker Hub...
docker compose pull
if errorlevel 1 (
  echo [WARN] docker compose pull failed, continue with local cache/build.
)

echo [INFO] Start services...
docker compose up -d --remove-orphans
if errorlevel 1 (
  echo [WARN] Start without build failed, retry with local build.
  docker compose up -d --build --remove-orphans
  if errorlevel 1 (
    echo [ERROR] Failed to start services.
    exit /b 1
  )
)

if not "%SQL_FILE%"=="" (
  if /I "%SQL_FILE%"=="AUTO" (
    echo [INFO] Import bundled SQL files: models\scripts\back_end_*.sql
    call docker\mysql\import-sql-dir.cmd "%MYSQL_DATABASE%" "models\scripts" "back_end_*.sql"
    if errorlevel 1 exit /b 1
  ) else (
    echo [INFO] Import custom SQL: %SQL_FILE%
    call docker\mysql\import-database.cmd "%MYSQL_DATABASE%" "%SQL_FILE%"
    if errorlevel 1 exit /b 1
  )

  echo [INFO] Recreate backend services to ensure new DB env is used...
  docker compose up -d --force-recreate python-backend java-backend
  if errorlevel 1 (
    echo [ERROR] Failed to recreate backend services.
    exit /b 1
  )
)

echo [DONE] Deployment finished.
echo [DONE] Frontend: http://localhost:%FRONTEND_PORT%
echo [DONE] Java API : http://localhost:%JAVA_PORT%
echo [DONE] Python API: http://localhost:%PYTHON_PORT%
exit /b 0

:usage
echo Usage: deploy.cmd ^<dockerhub_namespace^> [image_tag] [database_name] [sql_file_or_AUTO]
echo Example1: deploy.cmd yourname V1.0
echo Example2: deploy.cmd yourname V1.0 back_end_alice models\scripts\003_seed_data.sql
echo Example3: deploy.cmd yourname V1.0 back_end AUTO
exit /b 1
