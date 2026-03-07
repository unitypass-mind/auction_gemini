# Windows Scheduled Task Setup for Auction AI

$taskName = "AuctionAI_Weekly_Update"
$scriptPath = "C:\Users\unity\auction_gemini\scheduled_tasks\weekly_update.bat"
$workingDir = "C:\Users\unity\auction_gemini"

Write-Host "Creating scheduled task: $taskName" -ForegroundColor Green

# Remove existing task if exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create action
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workingDir

# Create trigger (Every Sunday at 3 AM)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

# Register task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Auction AI Weekly Data Collection and Model Retraining" -Force

Write-Host ""
Write-Host "SUCCESS! Task created:" -ForegroundColor Green
Write-Host "  Task Name: $taskName"
Write-Host "  Schedule: Every Sunday at 3:00 AM"
Write-Host "  Script: $scriptPath"
Write-Host ""
Write-Host "To run immediately, use:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName $taskName"
Write-Host ""

# Show task info
$taskInfo = Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo
Write-Host "Next Run Time: $($taskInfo.NextRunTime)" -ForegroundColor Cyan
