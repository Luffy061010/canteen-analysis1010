@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "LOGFILE=deploy.log"

set "RESET_DATA=0"
set "BUILD_IF_MISSING=1"
set "SKIP_PULL=0"
set "RETRY_COUNT=4"
set "RETRY_DELAY=8"

set "DOCKERHUB_NAMESPACE=local"
set "IMAGE_TAG=V1.0"
set "FRONTEND_PORT=80"
set "JAVA_PORT=8080"
set "PYTHON_PORT=8000"

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="-ResetData" (
	set "RESET_DATA=1"
	shift
	goto :parse_args
)
if /i "%~1"=="-NoBuildFallback" (
	set "BUILD_IF_MISSING=0"
	shift
	goto :parse_args
)
if /i "%~1"=="-SkipPull" (
	set "SKIP_PULL=1"
	shift
	goto :parse_args
)
if /i "%~1"=="-BuildIfMissing" (
	if "%~2"=="" (
		echo [ERROR] Missing value for -BuildIfMissing
		goto :fail
	)
	if /i "%~2"=="true" set "BUILD_IF_MISSING=1"
	if /i "%~2"=="false" set "BUILD_IF_MISSING=0"
	shift
	shift
	goto :parse_args
)
if /i "%~1"=="-RetryCount" (
	if "%~2"=="" (
		echo [ERROR] Missing value for -RetryCount
		goto :fail
	)
	set "RETRY_COUNT=%~2"
	shift
	shift
	goto :parse_args
)
if /i "%~1"=="-RetryDelaySec" (
	if "%~2"=="" (
		echo [ERROR] Missing value for -RetryDelaySec
		goto :fail
	)
	set "RETRY_DELAY=%~2"
	shift
	shift
	goto :parse_args
)

echo [ERROR] Unknown argument: %~1
goto :fail

:args_done

call :load_env

> "%LOGFILE%" echo ============================================================
>> "%LOGFILE%" echo Deploy started at %date% %time%
>> "%LOGFILE%" echo Working dir: %cd%
>> "%LOGFILE%" echo RESET_DATA=%RESET_DATA%, BUILD_IF_MISSING=%BUILD_IF_MISSING%, SKIP_PULL=%SKIP_PULL%
>> "%LOGFILE%" echo RETRY_COUNT=%RETRY_COUNT%, RETRY_DELAY=%RETRY_DELAY%
>> "%LOGFILE%" echo ============================================================

if not exist "docker-compose.yml" (
	echo [ERROR] docker-compose.yml not found in %cd%
	>> "%LOGFILE%" echo [ERROR] docker-compose.yml not found
	goto :fail
)

call :run_with_retry "Check Docker daemon" "docker version" 0
if errorlevel 1 goto :fail

if "%RESET_DATA%"=="1" (
	call :run_with_retry "Stop stack and remove volumes" "docker compose down -v" 0
	if errorlevel 1 goto :fail
) else (
	call :run_with_retry "Stop old containers" "docker compose down" 1
)

set "PULL_OK=1"
if not "%SKIP_PULL%"=="1" (
	call :run_with_retry "Pull images" "docker compose pull" 1
	if errorlevel 1 set "PULL_OK=0"
)

set "APP_IMAGE_1=%DOCKERHUB_NAMESPACE%/canteen-frontend:%IMAGE_TAG%"
set "APP_IMAGE_2=%DOCKERHUB_NAMESPACE%/canteen-python-backend:%IMAGE_TAG%"
set "APP_IMAGE_3=%DOCKERHUB_NAMESPACE%/canteen-java-backend:%IMAGE_TAG%"
set "APP_IMAGE_4=%DOCKERHUB_NAMESPACE%/canteen-mysql:%IMAGE_TAG%"

set "MISSING_IMAGES="
for %%I in ("%APP_IMAGE_1%" "%APP_IMAGE_2%" "%APP_IMAGE_3%" "%APP_IMAGE_4%") do (
	docker image inspect %%~I >nul 2>> "%LOGFILE%"
	if errorlevel 1 (
		if defined MISSING_IMAGES (
			set "MISSING_IMAGES=!MISSING_IMAGES!, %%~I"
		) else (
			set "MISSING_IMAGES=%%~I"
		)
	)
)

if defined MISSING_IMAGES (
	echo [WARN] Missing local images: !MISSING_IMAGES!
	>> "%LOGFILE%" echo [WARN] Missing local images: !MISSING_IMAGES!

	if "%BUILD_IF_MISSING%"=="0" (
		echo [ERROR] Images missing and build fallback is disabled.
		goto :fail
	)

	call :run_with_retry "Build missing images" "docker compose build" 0
	if errorlevel 1 goto :fail
) else (
	if "%PULL_OK%"=="0" (
		echo [WARN] Pull failed but required images exist locally. Continue with local cache.
		>> "%LOGFILE%" echo [WARN] Pull failed but local images are available.
	)
)

call :run_with_retry "Start stack without build" "docker compose up -d --remove-orphans --no-build" 1
if errorlevel 1 (
	if "%BUILD_IF_MISSING%"=="0" (
		echo [ERROR] Startup failed and build fallback is disabled.
		goto :fail
	)
	echo [WARN] Startup failed, retry with compose build + up.
	>> "%LOGFILE%" echo [WARN] Startup failed, retry with build + up

	call :run_with_retry "Build all services" "docker compose build" 0
	if errorlevel 1 goto :fail

	call :run_with_retry "Start stack after build" "docker compose up -d --remove-orphans --no-build" 0
	if errorlevel 1 goto :fail
)

call :wait_health mysql 240
if errorlevel 1 goto :fail
call :wait_health redis 240
if errorlevel 1 goto :fail

where curl >nul 2>nul
if errorlevel 1 (
	echo [WARN] curl not found. Skip HTTP readiness checks.
	>> "%LOGFILE%" echo [WARN] curl not found. Skip HTTP checks.
) else (
	call :wait_http "Python backend" "http://localhost:%PYTHON_PORT%/" 240
	if errorlevel 1 goto :fail
	call :wait_http "Java backend" "http://localhost:%JAVA_PORT%/system/status" 240
	if errorlevel 1 goto :fail
	call :wait_http "Frontend" "http://localhost:%FRONTEND_PORT%" 240
	if errorlevel 1 goto :fail
)

docker compose ps >> "%LOGFILE%" 2>&1

echo.
echo Deployment completed successfully.
echo Open: http://localhost:%FRONTEND_PORT%
echo Logs: %cd%\%LOGFILE%
if not "%CI%"=="true" pause
exit /b 0

:run_with_retry
set "STEP_NAME=%~1"
set "RUN_CMD=%~2"
set "ALLOW_FINAL_FAIL=%~3"
set /a ATTEMPT=1

:retry_loop
echo [INFO] %STEP_NAME% ^(attempt !ATTEMPT!/%RETRY_COUNT%^)
>> "%LOGFILE%" echo [INFO] %STEP_NAME% ^(attempt !ATTEMPT!/%RETRY_COUNT%^)

cmd /c "%RUN_CMD%" >> "%LOGFILE%" 2>&1
if not errorlevel 1 (
	echo [INFO] %STEP_NAME% succeeded
	>> "%LOGFILE%" echo [INFO] %STEP_NAME% succeeded
	exit /b 0
)

if !ATTEMPT! GEQ %RETRY_COUNT% (
	echo [WARN] %STEP_NAME% reached retry limit
	>> "%LOGFILE%" echo [WARN] %STEP_NAME% reached retry limit
	if "%ALLOW_FINAL_FAIL%"=="1" exit /b 1
	exit /b 1
)

set /a WAIT_SEC=%RETRY_DELAY%*ATTEMPT
if !WAIT_SEC! GTR 60 set /a WAIT_SEC=60
echo [WARN] %STEP_NAME% failed, retrying in !WAIT_SEC! seconds...
>> "%LOGFILE%" echo [WARN] %STEP_NAME% failed, retrying in !WAIT_SEC! seconds...
timeout /t !WAIT_SEC! /nobreak >nul
set /a ATTEMPT+=1
goto :retry_loop

:wait_health
set "CONTAINER_NAME=%~1"
set /a TIMEOUT_SEC=%~2
set /a ELAPSED=0

:wait_health_loop
set "HEALTH_STATUS="
for /f "delims=" %%i in ('docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" %CONTAINER_NAME% 2^>nul') do set "HEALTH_STATUS=%%i"

if /i "%HEALTH_STATUS%"=="healthy" (
	echo [INFO] %CONTAINER_NAME% is healthy
	>> "%LOGFILE%" echo [INFO] %CONTAINER_NAME% is healthy
	exit /b 0
)

if /i "%HEALTH_STATUS%"=="unhealthy" (
	echo [ERROR] %CONTAINER_NAME% is unhealthy
	>> "%LOGFILE%" echo [ERROR] %CONTAINER_NAME% is unhealthy
	exit /b 1
)

if %ELAPSED% GEQ %TIMEOUT_SEC% (
	echo [ERROR] Timeout waiting for %CONTAINER_NAME% health
	>> "%LOGFILE%" echo [ERROR] Timeout waiting for %CONTAINER_NAME% health
	exit /b 1
)

timeout /t 3 /nobreak >nul
set /a ELAPSED+=3
goto :wait_health_loop

:wait_http
set "HTTP_NAME=%~1"
set "HTTP_URL=%~2"
set /a HTTP_TIMEOUT=%~3
set /a HTTP_ELAPSED=0

:wait_http_loop
curl -fsS --max-time 8 "%HTTP_URL%" >nul 2>> "%LOGFILE%"
if not errorlevel 1 (
	echo [INFO] %HTTP_NAME% ready: %HTTP_URL%
	>> "%LOGFILE%" echo [INFO] %HTTP_NAME% ready: %HTTP_URL%
	exit /b 0
)

if %HTTP_ELAPSED% GEQ %HTTP_TIMEOUT% (
	echo [ERROR] Timeout waiting for %HTTP_NAME%: %HTTP_URL%
	>> "%LOGFILE%" echo [ERROR] Timeout waiting for %HTTP_NAME%: %HTTP_URL%
	exit /b 1
)

timeout /t 3 /nobreak >nul
set /a HTTP_ELAPSED+=3
goto :wait_http_loop

:load_env
if not exist ".env" (
	if exist ".env.example" (
		copy /Y ".env.example" ".env" >nul
		echo [INFO] Created .env from .env.example
	)
)

if not exist ".env" exit /b 0

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
	set "ENV_KEY=%%A"
	set "ENV_VAL=%%B"

	if defined ENV_KEY (
		if not "!ENV_KEY:~0,1!"=="#" (
			if /i "!ENV_KEY!"=="DOCKERHUB_NAMESPACE" set "DOCKERHUB_NAMESPACE=!ENV_VAL!"
			if /i "!ENV_KEY!"=="IMAGE_TAG" set "IMAGE_TAG=!ENV_VAL!"
			if /i "!ENV_KEY!"=="FRONTEND_PORT" set "FRONTEND_PORT=!ENV_VAL!"
			if /i "!ENV_KEY!"=="JAVA_PORT" set "JAVA_PORT=!ENV_VAL!"
			if /i "!ENV_KEY!"=="PYTHON_PORT" set "PYTHON_PORT=!ENV_VAL!"
		)
	)
)
exit /b 0

:fail
echo.
echo Deployment failed. See log: %cd%\%LOGFILE%
if exist "%LOGFILE%" (
	echo ---------- LOG TAIL ----------
	type "%LOGFILE%"
	echo ------------------------------
)
if not "%CI%"=="true" pause
exit /b 1
