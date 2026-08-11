# Restore the MongoDB database from a mongodump backup directory.
#
# This is DESTRUCTIVE: mongorestore is run with --drop, which drops each
# collection in the target database before restoring it from the backup.
#
# Required env vars (same names used in app/core/config.py):
#   MONGODB_HOST, MONGODB_PORT, MONGODB_DB, MONGODB_USER, MONGODB_PASSWORD
#
# Optional: MONGODB_AUTH_DB (defaults to MONGODB_DB).
#
# Usage:
#   .\scripts\restore_mongo.ps1 <backup_dir> --yes
#
# <backup_dir> is the directory produced by backup_mongo.ps1, e.g.
#   backups\mongo\20260101T120000Z
# (the directory that directly contains the "<db>" subdirectory of BSON files).
#
# Without --yes, the script only prints what it would do and exits without
# touching the database.

param(
    [Parameter(Position = 0)]
    [string]$BackupDir,

    [Parameter(Position = 1)]
    [string]$Confirm
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrEmpty($BackupDir)) {
    Write-Error "ERROR: missing backup directory argument. Usage: .\scripts\restore_mongo.ps1 <backup_dir> --yes"
    exit 1
}

if (-not (Test-Path $BackupDir -PathType Container)) {
    Write-Error "ERROR: backup directory not found: $BackupDir"
    exit 1
}

$requiredVars = @("MONGODB_HOST", "MONGODB_PORT", "MONGODB_DB", "MONGODB_USER", "MONGODB_PASSWORD")
foreach ($var in $requiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Error "ERROR: required environment variable $var is not set."
        exit 1
    }
}

if (-not (Get-Command mongorestore -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: mongorestore not found on PATH. Install the MongoDB Database Tools."
    exit 1
}

$AuthDb = $env:MONGODB_AUTH_DB
if ([string]::IsNullOrEmpty($AuthDb)) {
    $AuthDb = $env:MONGODB_DB
}

$SourceDbDir = Join-Path $BackupDir $env:MONGODB_DB

if ($Confirm -ne "--yes") {
    Write-Output "This would restore database '$($env:MONGODB_DB)' on $($env:MONGODB_HOST):$($env:MONGODB_PORT)"
    Write-Output "from backup directory: $SourceDbDir"
    Write-Output "using: mongorestore --drop (this DROPS existing collections first)"
    Write-Output ""
    Write-Output "No changes made. Re-run with --yes as the second argument to actually restore:"
    Write-Output "  .\scripts\restore_mongo.ps1 `"$BackupDir`" --yes"
    exit 0
}

if (-not (Test-Path $SourceDbDir -PathType Container)) {
    Write-Error "ERROR: expected database subdirectory not found: $SourceDbDir. Point <backup_dir> at the timestamped folder produced by backup_mongo.ps1."
    exit 1
}

& mongorestore `
    --host $env:MONGODB_HOST `
    --port $env:MONGODB_PORT `
    --db $env:MONGODB_DB `
    --username $env:MONGODB_USER `
    --password $env:MONGODB_PASSWORD `
    --authenticationDatabase $AuthDb `
    --drop `
    $SourceDbDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: mongorestore failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Output "Restore complete from: $SourceDbDir"
