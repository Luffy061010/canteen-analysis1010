param(
    [string]$ContainerName = "mysql",
    [string]$Database = "back_end",
    [string]$RootPassword = "123456",
    [string]$OutputFile = "models/scripts/003_seed_data.sql"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/4] Check container running: $ContainerName"
$running = docker ps --filter "name=^$ContainerName$" --format "{{.Names}}"
if (-not $running) {
    throw "Container $ContainerName is not running. Run: docker compose up -d"
}

Write-Host "[2/4] Check mysqldump availability"
docker exec $ContainerName sh -lc "mysqldump --version" | Out-Null

Write-Host "[3/4] Export database $Database to $OutputFile"
$targetPath = Join-Path (Get-Location) $OutputFile
$targetDir = Split-Path -Parent $targetPath
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$dumpCmd = "mysqldump -uroot -p'$RootPassword' --set-gtid-purged=OFF --single-transaction --routines --events --triggers '$Database'"
$dump = docker exec $ContainerName sh -lc $dumpCmd
$header = @(
    "-- Auto-generated real business data dump",
    "-- Generated at: $(Get-Date -Format \"yyyy-MM-dd HH:mm:ss\")",
    "-- Source container: $ContainerName",
    ""
) -join [Environment]::NewLine

($header + [Environment]::NewLine + ($dump -join [Environment]::NewLine)) | Set-Content -Path $targetPath -Encoding UTF8

Write-Host "[4/4] Finish"
Write-Host "Done. Generated: $OutputFile"
Write-Host "Next: docker compose down -v; docker compose up -d --build"
