@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"
set LOGFILE=deploy.log

echo =============================================== > "%LOGFILE%"
echo Deploy started at %date% %time% >> "%LOGFILE%"
echo Working dir: %cd% >> "%LOGFILE%"
echo =============================================== >> "%LOGFILE%"

echo [Check] docker-compose.yml exists?
if not exist "docker-compose.yml" (
	echo [ERROR] docker-compose.yml not found in %cd%
	echo [ERROR] docker-compose.yml not found in %cd% >> "%LOGFILE%"
	goto :fail
)

echo [1/5] Pull images from Docker Hub
docker compose pull >> "%LOGFILE%" 2>&1
if errorlevel 1 (
	echo Pull failed, try docker login and retry...
	echo Pull failed, try docker login and retry... >> "%LOGFILE%"
	docker login >> "%LOGFILE%" 2>&1
	if errorlevel 1 goto :fail
	docker compose pull >> "%LOGFILE%" 2>&1
	if errorlevel 1 goto :fail
)

echo [2/5] Reset old containers and volumes
docker compose down -v >> "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

echo [3/5] Start services
docker compose up -d >> "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

echo [4/5] Import database dump
docker exec canteen-mysql mysql -uroot -p123456 back_end -e "source /docker-entrypoint-initdb.d/003_back_end_data.sql" >> "%LOGFILE%" 2>&1
if errorlevel 1 goto :fail

echo [5/5] Health check
docker compose ps >> "%LOGFILE%" 2>&1

echo.
echo Deployment completed.
echo Open: http://localhost
echo Logs: %cd%\%LOGFILE%
pause
exit /b 0

:fail
echo.
echo Deployment failed. See log: %cd%\%LOGFILE%
echo ---------- LOG (tail) ----------
powershell -NoProfile -Command "if (Test-Path '%LOGFILE%') { Get-Content '%LOGFILE%' -Tail 80 }"
echo --------------------------------
pause
exit /b 1
