@echo off
setlocal EnableExtensions EnableDelayedExpansion

if "%~1"=="" goto :usage

set "DB_NAME=%~1"
set "SQL_DIR=%~2"
set "SQL_PATTERN=%~3"

if "%SQL_DIR%"=="" set "SQL_DIR=models\scripts"
if "%SQL_PATTERN%"=="" set "SQL_PATTERN=back_end_*.sql"

call :validate_db_name "%DB_NAME%"
if errorlevel 1 (
  echo [ERROR] Invalid database name: %DB_NAME%
  echo [ERROR] Allowed characters: letters, numbers, underscore.
  exit /b 1
)

for %%I in ("%SQL_DIR%") do set "SQL_DIR_ABS=%%~fI"
if not exist "%SQL_DIR_ABS%" (
  echo [ERROR] SQL directory not found: %SQL_DIR%
  exit /b 1
)

set "MYSQL_RUNNING="
for /f "delims=" %%S in ('docker compose ps --services --status running 2^>nul') do (
  if /I "%%S"=="mysql" set "MYSQL_RUNNING=1"
)
if not defined MYSQL_RUNNING (
  echo [ERROR] mysql service is not running.
  echo [ERROR] Run: docker compose up -d mysql
  exit /b 1
)

set /a IMPORTED_COUNT=0
echo [INFO] Import SQL files from: %SQL_DIR_ABS%\%SQL_PATTERN%

for /f "delims=" %%F in ('dir /b /on "%SQL_DIR_ABS%\%SQL_PATTERN%" 2^>nul') do (
  set /a IMPORTED_COUNT+=1
  echo [INFO] [!IMPORTED_COUNT!] Importing: %%F
  call docker\mysql\import-database.cmd "%DB_NAME%" "%SQL_DIR_ABS%\%%F"
  if errorlevel 1 (
    echo [ERROR] Failed while importing: %%F
    exit /b 1
  )
)

if %IMPORTED_COUNT% EQU 0 (
  echo [ERROR] No SQL files matched: %SQL_DIR_ABS%\%SQL_PATTERN%
  exit /b 1
)

echo [DONE] Imported %IMPORTED_COUNT% SQL files into %DB_NAME%.
exit /b 0

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
echo Usage: docker\mysql\import-sql-dir.cmd ^<database_name^> [sql_dir] [sql_pattern]
echo Example1: docker\mysql\import-sql-dir.cmd back_end
echo Example2: docker\mysql\import-sql-dir.cmd back_end models\scripts back_end_*.sql
exit /b 1