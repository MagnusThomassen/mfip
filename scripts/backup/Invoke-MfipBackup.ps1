# Invoke-MfipBackup.ps1
# MFIP daily backup script — restic to Backblaze B2
# Runs via Task Scheduler at 02:00 daily
# Logs to C:\MFIP\runtime\backup-logs\YYYY-MM-DD.log

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Paths ────────────────────────────────────────────────────────────────────
$EnvFile     = "C:\MFIP\repo\.env"
$BackupRoot  = "C:\MFIP"
$ExcludeFile = "C:\MFIP\repo\.resticignore"
$LogDir      = "C:\MFIP\runtime\backup-logs"
$LogFile     = Join-Path $LogDir ((Get-Date -Format "yyyy-MM-dd") + ".log")

# ── Logging helper ───────────────────────────────────────────────────────────
function Write-Log {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

# ── Start ────────────────────────────────────────────────────────────────────
Write-Log "=== MFIP Backup started ==="

# ── Load .env ────────────────────────────────────────────────────────────────
if (-not (Test-Path $EnvFile)) {
    Write-Log "ERROR: .env not found at $EnvFile"
    exit 1
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*?)\s*=\s*(.*)\s*$') {
        [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
    }
}

# ── Validate required env vars ───────────────────────────────────────────────
$required = @("MFIP_B2_KEY_ID", "MFIP_B2_APP_KEY", "MFIP_B2_BUCKET", "MFIP_RESTIC_PASSWORD")
foreach ($key in $required) {
    if (-not [System.Environment]::GetEnvironmentVariable($key, "Process")) {
        Write-Log "ERROR: Required env var $key is missing or empty"
        exit 1
    }
}

# ── Set restic env vars ───────────────────────────────────────────────────────
$env:B2_ACCOUNT_ID  = [System.Environment]::GetEnvironmentVariable("MFIP_B2_KEY_ID", "Process")
$env:B2_ACCOUNT_KEY = [System.Environment]::GetEnvironmentVariable("MFIP_B2_APP_KEY", "Process")
$env:RESTIC_PASSWORD = [System.Environment]::GetEnvironmentVariable("MFIP_RESTIC_PASSWORD", "Process")
$env:RESTIC_REPOSITORY = "b2:" + [System.Environment]::GetEnvironmentVariable("MFIP_B2_BUCKET", "Process")

Write-Log "Repository: $env:RESTIC_REPOSITORY"
Write-Log "Backup source: $BackupRoot"

# ── Run backup ────────────────────────────────────────────────────────────────
try {
    $output = & restic backup $BackupRoot `
        --exclude-file $ExcludeFile `
        --json `
        2>&1

    # Write all output to screen; write only the summary line to log file
    $output | ForEach-Object {
        Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $_"
        try {
            $parsed = $_ | ConvertFrom-Json -ErrorAction Stop
            if ($parsed.message_type -eq "summary") {
                Write-Log "SUMMARY: files_new=$($parsed.files_new) files_changed=$($parsed.files_changed) data_added_packed=$([math]::Round($parsed.data_added_packed/1KB,1))KB duration=$([math]::Round($parsed.total_duration,1))s snapshot=$($parsed.snapshot_id.Substring(0,8))"
            }
        } catch {}
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: restic backup exited with code $LASTEXITCODE"
        exit 2
    }

    Write-Log "Backup completed successfully"
    exit 0
}
catch {
    Write-Log "EXCEPTION: $_"
    exit 3
}


