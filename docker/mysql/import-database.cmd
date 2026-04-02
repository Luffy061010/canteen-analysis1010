@echo off
setlocal EnableExtensions

if "%~1"=="" goto :usage
if "%~2"=="" goto :usage

set "DB_NAME=%~1"
set "SQL_FILE=%~2"

call :validate_db_name "%DB_NAME%"
if errorlevel 1 (
  echo [ERROR] Invalid database name: %DB_NAME%
  echo [ERROR] Allowed characters: letters, numbers, underscore.
  exit /b 1
)

if not exist "%SQL_FILE%" (
  echo [ERROR] SQL file not found: %SQL_FILE%
  exit /b 1
)

for %%I in ("%SQL_FILE%") do set "SQL_FILE_ABS=%%~fI"

set "MYSQL_RUNNING="
for /f "delims=" %%S in ('docker compose ps --services --status running 2^>nul') do (
  if /I "%%S"=="mysql" set "MYSQL_RUNNING=1"
)
if not defined MYSQL_RUNNING (
  echo [ERROR] mysql service is not running.
  echo [ERROR] Run: docker compose up -d mysql
  exit /b 1
)

echo [INFO] Copy SQL into mysql container...
docker compose cp "%SQL_FILE_ABS%" mysql:/tmp/import.sql
if errorlevel 1 (
  echo [ERROR] Failed to copy SQL into mysql container.
  exit /b 1
)

echo [INFO] Create database if not exists: %DB_NAME%
docker compose exec -T mysql sh -lc "mysql -uroot -p\"$MYSQL_ROOT_PASSWORD\" -e 'CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'"
if errorlevel 1 goto :import_fail

echo [INFO] Import SQL into database: %DB_NAME%
docker compose exec -T mysql sh -lc "mysql -uroot -p\"$MYSQL_ROOT_PASSWORD\" %DB_NAME% < /tmp/import.sql"
if errorlevel 1 goto :import_fail

docker compose exec -T mysql sh -lc "rm -f /tmp/import.sql" >nul 2>&1

echo [DONE] Database import completed.
echo [DONE] Database: %DB_NAME%
echo [DONE] SQL file: %SQL_FILE_ABS%
exit /b 0

:import_fail
docker compose exec -T mysql sh -lc "rm -f /tmp/import.sql" >nul 2>&1
echo [ERROR] Import failed.
exit /b 1

:validate_db_name
setlocal EnableDelayedExpansion
set "DB_CHECK=%~1"
if "!DB_CHECK!"=="" (
  endlocal & exit /b 1
)
for %%C in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9 _) do set "DB_CHECK=!DB_CHECK:%%C=!"
if defined DB_CHECK (
  endlocal & exit /b 1
)
endlocal & exit /b 0

:usage
echo Usage: docker\mysql\import-database.cmd ^<database_name^> ^<sql_file_path^>
echo Example: docker\mysql\import-database.cmd back_end_alice models\scripts\003_seed_data.sql
exit /b 1
