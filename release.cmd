@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set VERSION=v1.0.0
set FRONTEND=lln1010/1010-frontend:%VERSION%
set JAVA=lln1010/1010-java:%VERSION%
set PYTHON=lln1010/1010-python:%VERSION%

echo [1/9] Docker login
docker login
if errorlevel 1 exit /b 1

echo [2/9] Build frontend image %FRONTEND%
docker build -f docker/frontend/Dockerfile -t %FRONTEND% .
if errorlevel 1 exit /b 1

echo [3/9] Build python image %PYTHON%
docker build -f docker/python/Dockerfile -t %PYTHON% .
if errorlevel 1 exit /b 1

echo [4/9] Build java image %JAVA%
docker build -f docker/backend/Dockerfile -t %JAVA% .
if errorlevel 1 exit /b 1

echo [5/9] Push frontend version tag
docker push %FRONTEND%
if errorlevel 1 exit /b 1

echo [6/9] Push python version tag
docker push %PYTHON%
if errorlevel 1 exit /b 1

echo [7/9] Push java version tag
docker push %JAVA%
if errorlevel 1 exit /b 1

echo [8/9] Tag latest images
docker tag %FRONTEND% lln1010/1010-frontend:latest
docker tag %PYTHON% lln1010/1010-python:latest
docker tag %JAVA% lln1010/1010-java:latest

echo [9/9] Push latest images
docker push lln1010/1010-frontend:latest
docker push lln1010/1010-python:latest
docker push lln1010/1010-java:latest
if errorlevel 1 exit /b 1

echo.
echo Release done: %VERSION% ^(fixed^)
exit /b 0
