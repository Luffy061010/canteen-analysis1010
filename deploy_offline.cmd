@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set VERSION=V1.0.0
set IMAGE_ARCHIVE=images\canteen-images-%VERSION%.tar
set MAX_WAIT_SECONDS=240

echo [0/7] Preflight checks
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker command not found. Please install Docker Desktop first.
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker is not running. Please start Docker Desktop and retry.
  exit /b 1
)

docker compose version >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker Compose plugin not available. Please update Docker Desktop.
  exit /b 1
)

echo [1/7] Check image archive
if not exist "%IMAGE_ARCHIVE%" (
  echo [ERROR] Missing image archive: %IMAGE_ARCHIVE%
  exit /b 1
)

echo [2/7] Load images into local Docker
docker load -i "%IMAGE_ARCHIVE%" || goto :fail

echo [3/7] Reset old containers and data volume
docker compose down -v

echo [4/7] Start services without pulling from network
docker compose up -d --pull never || goto :fail

echo [5/7] Wait for containers startup
set /a waited=0
:wait_loop
for /f "delims=" %%i in ('docker compose ps -q mysql') do set MYSQL_ID=%%i
if "%MYSQL_ID%"=="" goto :wait_next
for /f "delims=" %%h in ('docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" %MYSQL_ID%') do set MYSQL_HEALTH=%%h
if /I "%MYSQL_HEALTH%"=="healthy" goto :wait_ok

:wait_next
if %waited% GEQ %MAX_WAIT_SECONDS% goto :wait_timeout
timeout /t 5 /nobreak >nul
set /a waited+=5
goto :wait_loop

:wait_ok
echo [6/7] Verify status
docker compose ps

echo [7/7] Final endpoint check
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://localhost' -UseBasicParsing -TimeoutSec 10; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo [WARN] Containers are up, but homepage check failed. Please wait 10-30 seconds and open http://localhost manually.
  echo [HINT] Use 'docker compose logs frontend' for frontend logs.
) else (
  echo [OK] Homepage is reachable: http://localhost
)

echo.
echo Offline deployment succeeded. Open: http://localhost
exit /b 0

:wait_timeout
echo.
echo [ERROR] Startup timeout after %MAX_WAIT_SECONDS%s. Containers may still be initializing.
echo [HINT] Run the following commands to inspect:
echo        docker compose ps
echo        docker compose logs mysql
echo        docker compose logs backend
echo        docker compose logs frontend
exit /b 1

:fail
echo.
echo Offline deployment failed.
echo [HINT] Run 'docker compose ps' and 'docker compose logs -f' to troubleshoot.
exit /b 1
