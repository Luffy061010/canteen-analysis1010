param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseName,

    [Parameter(Mandatory = $true)]
    [string]$SqlFile,

    [string]$ComposeFile = "docker-compose.yml"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($DatabaseName -notmatch "^[A-Za-z0-9_]+$") {
    throw "DatabaseName can only include letters, numbers, and underscore."
}

$workspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$composePath = Join-Path $workspaceRoot $ComposeFile

if (-not (Test-Path $composePath)) {
    throw "Compose file not found: $composePath"
}

if (-not (Test-Path $SqlFile)) {
    throw "SQL file not found: $SqlFile"
}

$sqlFullPath = (Resolve-Path -Path $SqlFile).Path
Set-Location $workspaceRoot

$runningServices = @(docker compose -f $composePath ps --services --status running)
if ($LASTEXITCODE -ne 0) {
    throw "Failed to query compose services."
}

if (-not ($runningServices -contains "mysql")) {
    throw "MySQL service is not running. Run: docker compose -f $composePath up -d mysql"
}

$tempSqlPath = "/tmp/import.sql"

Write-Host "Copy SQL to container..."
docker compose -f $composePath cp $sqlFullPath "mysql:$tempSqlPath"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to copy SQL into mysql container."
}

try {
    $createCommand = "mysql -uroot -p`"`$MYSQL_ROOT_PASSWORD`" -e `"CREATE DATABASE IF NOT EXISTS $DatabaseName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`""
    docker compose -f $composePath exec -T mysql sh -lc $createCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create database: $DatabaseName"
    }

    $importCommand = "mysql -uroot -p`"`$MYSQL_ROOT_PASSWORD`" $DatabaseName < $tempSqlPath"
    docker compose -f $composePath exec -T mysql sh -lc $importCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to import SQL into database: $DatabaseName"
    }
}
finally {
    docker compose -f $composePath exec -T mysql sh -lc "rm -f $tempSqlPath" | Out-Null
}

Write-Host "Import completed."
Write-Host "Database: $DatabaseName"
Write-Host "Source SQL: $sqlFullPath"
