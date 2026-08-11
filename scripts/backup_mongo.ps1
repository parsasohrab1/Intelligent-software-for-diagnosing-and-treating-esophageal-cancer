# Backup the MongoDB database using mongodump.
#
# Required env vars (same names used in app/core/config.py):
#   MONGODB_HOST, MONGODB_PORT, MONGODB_DB, MONGODB_USER, MONGODB_PASSWORD
#
# Optional: MONGODB_AUTH_DB (defaults to MONGODB_DB) if the user was created
# against a different authentication database (e.g. "admin").
#
# Output: backups\mongo\<timestamp>\<db>\...
#
# Usage:
#   .\scripts\backup_mongo.ps1

$ErrorActionPreference = "Stop"

$requiredVars = @("MONGODB_HOST", "MONGODB_PORT", "MONGODB_DB", "MONGODB_USER", "MONGODB_PASSWORD")
foreach ($var in $requiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Error "ERROR: required environment variable $var is not set."
        exit 1
    }
}

if (-not (Get-Command mongodump -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: mongodump not found on PATH. Install the MongoDB Database Tools."
    exit 1
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$OutDir = Join-Path $RepoRoot "backups\mongo\$Timestamp"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$AuthDb = $env:MONGODB_AUTH_DB
if ([string]::IsNullOrEmpty($AuthDb)) {
    $AuthDb = $env:MONGODB_DB
}

& mongodump `
    --host $env:MONGODB_HOST `
    --port $env:MONGODB_PORT `
    --db $env:MONGODB_DB `
    --username $env:MONGODB_USER `
    --password $env:MONGODB_PASSWORD `
    --authenticationDatabase $AuthDb `
    --out $OutDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: mongodump failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Output "Backup written to: $OutDir"
