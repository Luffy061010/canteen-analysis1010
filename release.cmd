@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set VERSION=v1.0.0
set FRONTEND=lln1010/1010-frontend:%VERSION%
set JAVA=lln1010/1010-java:%VERSION%
set PYTHON=lln1010/1010-python:%VERSION%
set PYTHON_BUILD_ARGS=

if not "%PIP_INDEX_URL%"=="" (
	set PYTHON_BUILD_ARGS=%PYTHON_BUILD_ARGS% --build-arg PIP_INDEX_URL=%PIP_INDEX_URL%
)
if not "%PIP_EXTRA_INDEX_URL%"=="" (
	set PYTHON_BUILD_ARGS=%PYTHON_BUILD_ARGS% --build-arg PIP_EXTRA_INDEX_URL=%PIP_EXTRA_INDEX_URL%
)

echo [1/7] Docker login
docker login
if errorlevel 1 exit /b 1

echo [2/7] Build frontend image %FRONTEND%
docker build -f docker/frontend/Dockerfile -t %FRONTEND% .
if errorlevel 1 exit /b 1

echo [3/7] Build python image %PYTHON%
docker build %PYTHON_BUILD_ARGS% -f docker/python/Dockerfile -t %PYTHON% .
if errorlevel 1 exit /b 1

echo [4/7] Build java image %JAVA%
docker build -f docker/backend/Dockerfile -t %JAVA% .
if errorlevel 1 exit /b 1

echo [5/7] Push frontend version tag
docker push %FRONTEND%
if errorlevel 1 exit /b 1

echo [6/7] Push python version tag
docker push %PYTHON%
if errorlevel 1 exit /b 1

echo [7/7] Push java version tag
docker push %JAVA%
if errorlevel 1 exit /b 1

echo.
echo Release done: %VERSION% ^(fixed^)
exit /b 0
