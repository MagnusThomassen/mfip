# Invoke-MfipPruneReminder.ps1
# Runs on the 2nd of each month via Task Scheduler.
# Pops a Windows toast notification reminding Magnus to verify the prune ran.

$LogDir = "C:\MFIP\runtime\backup-logs"
$today = Get-Date -Format "yyyy-MM-dd"
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")

# Check if prune log exists from yesterday (1st of month)
$pruneLog = Get-ChildItem $LogDir -Filter "*$yesterday*prune*" -ErrorAction SilentlyContinue

if ($pruneLog) {
    $status = "Prune log found: $($pruneLog.Name). Verify it shows no errors."
    $urgency = "informational"
} else {
    $status = "No prune log found for $yesterday. Task Scheduler may have missed the run. Check manually."
    $urgency = "critical"
}

# Windows toast notification via BurntToast or fallback to balloon
try {
    Add-Type -AssemblyName System.Windows.Forms
    $notification = New-Object System.Windows.Forms.NotifyIcon
    $notification.Icon = [System.Drawing.SystemIcons]::Information
    $notification.BalloonTipTitle = "MFIP — Monthly Prune Check"
    $notification.BalloonTipText = $status
    $notification.BalloonTipIcon = if ($urgency -eq "critical") { "Warning" } else { "Info" }
    $notification.Visible = $true
    $notification.ShowBalloonTip(10000)
    Start-Sleep -Seconds 11
    $notification.Dispose()
} catch {
    # Fallback: write to a reminder file Magnus will see
    $reminderFile = "C:\MFIP\runtime\PRUNE_CHECK_REQUIRED_$today.txt"
    "MFIP Monthly Prune Check — $today`n$status" | Set-Content $reminderFile -Encoding UTF8
}
