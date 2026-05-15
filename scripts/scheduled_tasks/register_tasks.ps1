<#
.SYNOPSIS
Register all MFIP scheduled tasks on this machine.

.DESCRIPTION
Idempotent: unregisters existing tasks of the same name before
re-registering, so this script can be re-run after an XML
change. Run as the user who owns the tasks (not as
administrator, per the InteractiveToken logon type).

Tasks registered:
- MFIP-Backup           (daily 02:00) — restic backup to B2
- MFIP-Prune            (monthly)     — restic prune
- MFIP-PruneReminder                  — restic prune reminder
- MFIP-NightlyLogExport (daily 02:00) — export decision_log and
                                         security_log to logs-archive

.NOTES
The backup tasks live under scripts/backup/ (legacy path
from the 2026-05-10 backup infrastructure decision) and the
nightly log export task lives under scripts/scheduled_tasks/
(per the Python Logistics Layer decision). Future
consolidation would move all scheduled task XML under
scripts/scheduled_tasks/ for naming uniformity. Not in scope
for PR-C; tracked via worklog 2026-05-15 entry.
#>

$repoRoot = "C:\MFIP\repo"

$tasks = @(
    @{
        Name    = "MFIP-Backup"
        XmlPath = Join-Path $repoRoot "scripts\backup\Task-MfipBackup.xml"
    },
    @{
        Name    = "MFIP-Prune"
        XmlPath = Join-Path $repoRoot "scripts\backup\Task-MfipPrune.xml"
    },
    @{
        Name    = "MFIP-PruneReminder"
        XmlPath = Join-Path $repoRoot "scripts\backup\Task-MfipPruneReminder.xml"
    },
    @{
        Name    = "MFIP-NightlyLogExport"
        XmlPath = Join-Path $repoRoot "scripts\scheduled_tasks\Task-NightlyLogExport.xml"
    }
)

foreach ($t in $tasks) {
    if (-not (Test-Path -Path $t.XmlPath)) {
        Write-Warning "Skipping $($t.Name): XML not found at $($t.XmlPath)"
        continue
    }
    $existing = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false
    }
    $xml = Get-Content -Path $t.XmlPath -Raw
    Register-ScheduledTask -Xml $xml -TaskName $t.Name -User $env:USERNAME | Out-Null
    Write-Host "Registered: $($t.Name)"
}
