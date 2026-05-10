# Invoke-MfipPrune.ps1
# MFIP monthly prune script — restic retention enforcement + repo check
# Runs via Task Scheduler on 1st of month at 04:00
# Also prunes backup-logs older than 90 days
# Policy: keep-daily 30, keep-weekly 12, keep-monthly 12

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Paths ────────────────────────────────────────────────────────────────────
$EnvFile  = "C:\MFIP\repo\.env"
$LogDir   = "C:\MFIP\runtime\backup-logs"
$LogFile  = Join-Path $LogDir ((Get-Date -Format "yyyy-MM-dd") + "-prune.log")

# ── Logging helper ───────────────────────────────────────────────────────────
function Write-Log {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

# ── Start ────────────────────────────────────────────────────────────────────
Write-Log "=== MFIP Prune started ==="

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

# ── Set restic env vars ───────────────────────────────────────────────────────
$env:B2_ACCOUNT_ID   = [System.Environment]::GetEnvironmentVariable("MFIP_B2_KEY_ID", "Process")
$env:B2_ACCOUNT_KEY  = [System.Environment]::GetEnvironmentVariable("MFIP_B2_APP_KEY", "Process")
$env:RESTIC_PASSWORD = [System.Environment]::GetEnvironmentVariable("MFIP_RESTIC_PASSWORD", "Process")
$env:RESTIC_REPOSITORY = "b2:" + [System.Environment]::GetEnvironmentVariable("MFIP_B2_BUCKET", "Process")

Write-Log "Repository: $env:RESTIC_REPOSITORY"

# ── Forget + prune ────────────────────────────────────────────────────────────
Write-Log "Running forget --prune (policy: daily=30, weekly=12, monthly=12)..."
try {
    $output = & restic forget --keep-daily 30 --keep-weekly 12 --keep-monthly 12 --prune 2>&1
    $output | ForEach-Object { Write-Log $_ }

    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: restic forget exited with code $LASTEXITCODE"
        exit 2
    }
    Write-Log "Forget + prune completed successfully"
}
catch {
    Write-Log "EXCEPTION during forget: $_"
    exit 3
}

# ── Integrity check ───────────────────────────────────────────────────────────
Write-Log "Running restic check..."
try {
    $output = & restic check 2>&1
    $output | ForEach-Object { Write-Log $_ }

    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: restic check failed with code $LASTEXITCODE — repository may need attention"
        exit 4
    }
    Write-Log "Repository check passed"
}
catch {
    Write-Log "EXCEPTION during check: $_"
    exit 5
}

# ── Prune old log files (90-day retention) ────────────────────────────────────
Write-Log "Pruning backup-logs older than 90 days..."
$cutoff = (Get-Date).AddDays(-90)
$pruned = 0
Get-ChildItem $LogDir -File | Where-Object { $_.LastWriteTime -lt $cutoff } | ForEach-Object {
    Remove-Item $_.FullName -Force
    $pruned++
}
Write-Log "Log pruning complete — $pruned file(s) removed"

Write-Log "=== MFIP Prune finished ==="
exit 0
