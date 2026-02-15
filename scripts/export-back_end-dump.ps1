param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$User = "root",
    [string]$Password = "123456",
    [string]$Database = "back_end",
    [string]$OutputFile = "docker/mysql/init/003_back_end_data.sql"
)

$ErrorActionPreference = "Stop"

Write-Host "Exporting database '$Database' to '$OutputFile' ..."

$outputDir = Split-Path -Path $OutputFile -Parent
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$dumpArgs = @(
    "--host=$HostName",
    "--port=$Port",
    "--user=$User",
    "--password=$Password",
    "--default-character-set=utf8mb4",
    "--set-gtid-purged=OFF",
    "--single-transaction",
    "--routines",
    "--events",
    "--triggers",
    "$Database"
)

if (Get-Command mysqldump -ErrorAction SilentlyContinue) {
    & mysqldump @dumpArgs | Out-File -Encoding utf8 -FilePath $OutputFile
}
elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    $workspace = (Get-Location).Path
    $containerOutput = "/work/" + ($OutputFile -replace '\\', '/')
    $containerError = "/work/docker/mysql/init/003_back_end_data.err.log"
    $containerHost = $HostName
    if ($HostName -eq "127.0.0.1" -or $HostName -eq "localhost") {
        $containerHost = "host.docker.internal"
    }

    $dockerCmd = "mysqldump --host=$containerHost --port=$Port --user=$User --password=$Password --default-character-set=utf8mb4 --set-gtid-purged=OFF --single-transaction --routines --events --triggers $Database > $containerOutput 2> $containerError"

    & docker run --rm -v "${workspace}:/work" mysql:8.0 sh -c $dockerCmd
}
else {
    throw "Neither mysqldump nor docker is available in PATH."
}

$dumpFile = Get-Item -Path $OutputFile -ErrorAction Stop
if ($dumpFile.Length -le 0) {
    $errPath = "docker/mysql/init/003_back_end_data.err.log"
    if (Test-Path $errPath) {
        Write-Host "mysqldump error log:"
        Get-Content $errPath
    }
    throw "Export failed: output SQL file is empty. Check MySQL host/port/user/password and database name."
}

Write-Host "Export completed: $OutputFile"
