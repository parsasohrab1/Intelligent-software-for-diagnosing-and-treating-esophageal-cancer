# Restore the PostgreSQL database from a pg_dump custom-format backup file.
#
# This is DESTRUCTIVE: existing objects in the target database are dropped
# (--clean --if-exists) before being recreated from the backup.
#
# Required env vars (same names used in app/core/config.py / docker-compose.prod.yml):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#
# Usage:
#   .\scripts\restore_postgres.ps1 <backup_file> --yes
#
# Without --yes, the script only prints what it would do and exits without
# touching the database.

param(
    [Parameter(Position = 0)]
    [string]$BackupFile,

    [Parameter(Position = 1)]
    [string]$Confirm
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrEmpty($BackupFile)) {
    Write-Error "ERROR: missing backup file argument. Usage: .\scripts\restore_postgres.ps1 <backup_file> --yes"
    exit 1
}

if (-not (Test-Path $BackupFile)) {
    Write-Error "ERROR: backup file not found: $BackupFile"
    exit 1
}

$requiredVars = @("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
foreach ($var in $requiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Error "ERROR: required environment variable $var is not set."
        exit 1
    }
}

if (-not (Get-Command pg_restore -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: pg_restore not found on PATH. Install the PostgreSQL client tools."
    exit 1
}

if ($Confirm -ne "--yes") {
    Write-Output "This would restore database '$($env:POSTGRES_DB)' on $($env:POSTGRES_HOST):$($env:POSTGRES_PORT)"
    Write-Output "from backup file: $BackupFile"
    Write-Output "using: pg_restore --clean --if-exists (this DROPS existing objects first)"
    Write-Output ""
    Write-Output "No changes made. Re-run with --yes as the second argument to actually restore:"
    Write-Output "  .\scripts\restore_postgres.ps1 `"$BackupFile`" --yes"
    exit 0
}

$env:PGPASSWORD = $env:POSTGRES_PASSWORD

try {
    & pg_restore `
        -h $env:POSTGRES_HOST `
        -p $env:POSTGRES_PORT `
        -U $env:POSTGRES_USER `
        -d $env:POSTGRES_DB `
        --clean `
        --if-exists `
        $BackupFile

    if ($LASTEXITCODE -ne 0) {
        Write-Error "ERROR: pg_restore failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}
finally {
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Output "Restore complete from: $BackupFile"
