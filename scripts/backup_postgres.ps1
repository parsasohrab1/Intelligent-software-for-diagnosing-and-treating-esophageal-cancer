# Backup the PostgreSQL database using pg_dump (custom format).
#
# Required env vars (same names used in app/core/config.py / docker-compose.prod.yml):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#
# Output: backups\postgres\<db>_<timestamp>.dump
#
# Usage:
#   .\scripts\backup_postgres.ps1

$ErrorActionPreference = "Stop"

$requiredVars = @("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
foreach ($var in $requiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Error "ERROR: required environment variable $var is not set."
        exit 1
    }
}

if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: pg_dump not found on PATH. Install the PostgreSQL client tools."
    exit 1
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackupDir = Join-Path $RepoRoot "backups\postgres"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BackupFile = Join-Path $BackupDir "$($env:POSTGRES_DB)_$Timestamp.dump"

$env:PGPASSWORD = $env:POSTGRES_PASSWORD

try {
    & pg_dump `
        -h $env:POSTGRES_HOST `
        -p $env:POSTGRES_PORT `
        -U $env:POSTGRES_USER `
        -d $env:POSTGRES_DB `
        -Fc `
        -f $BackupFile

    if ($LASTEXITCODE -ne 0) {
        Write-Error "ERROR: pg_dump failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}
finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Output "Backup written to: $BackupFile"
