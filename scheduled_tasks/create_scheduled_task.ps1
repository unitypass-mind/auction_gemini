# ====================================
# Windows 작업 스케줄러 자동 등록
# PowerShell 스크립트
# ====================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows 작업 스케줄러 자동 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[오류] 관리자 권한이 필요합니다!" -ForegroundColor Red
    Write-Host ""
    Write-Host "해결 방법:" -ForegroundColor Yellow
    Write-Host "1. PowerShell을 우클릭" -ForegroundColor Yellow
    Write-Host "2. '관리자 권한으로 실행' 선택" -ForegroundColor Yellow
    Write-Host "3. 다음 명령어 실행:" -ForegroundColor Yellow
    Write-Host "   cd C:\Users\unity\auction_gemini\scheduled_tasks" -ForegroundColor White
    Write-Host "   .\create_scheduled_task.ps1" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "[확인] 관리자 권한으로 실행 중..." -ForegroundColor Green
Write-Host ""

# 작업 경로
$taskName = "경매AI주간업데이트"
$taskPath = "C:\Users\unity\auction_gemini\scheduled_tasks\weekly_update.bat"
$workingDir = "C:\Users\unity\auction_gemini"

# 기존 작업 확인 및 삭제
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[알림] 기존 작업이 존재합니다. 삭제 중..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host ""
}

# 작업 동작 정의
$action = New-ScheduledTaskAction -Execute $taskPath -WorkingDirectory $workingDir

# 트리거 정의 (매주 일요일 오전 3시)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am

# 설정 정의
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# 주체 정의 (최고 권한으로 실행)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -RunLevel Highest `
    -LogonType Interactive

Write-Host "[진행] 작업 스케줄러 등록 중..." -ForegroundColor Cyan
Write-Host ""

try {
    # 작업 등록
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "경매 AI 모델 주간 자동 업데이트 (데이터 수집 + 재학습)" `
        -Force | Out-Null

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[성공] 작업 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "작업 이름: $taskName" -ForegroundColor White
    Write-Host "실행 시간: 매주 일요일 오전 3:00" -ForegroundColor White
    Write-Host "실행 파일: $taskPath" -ForegroundColor White
    Write-Host "작업 경로: $workingDir" -ForegroundColor White
    Write-Host ""
    Write-Host "확인 방법:" -ForegroundColor Yellow
    Write-Host "1. 시작 메뉴 > 작업 스케줄러 검색" -ForegroundColor White
    Write-Host "2. '$taskName' 작업 확인" -ForegroundColor White
    Write-Host ""
    Write-Host "즉시 테스트 실행:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
    Write-Host ""

    # 작업 정보 표시
    $task = Get-ScheduledTask -TaskName $taskName
    Write-Host "등록된 작업 상태:" -ForegroundColor Cyan
    Write-Host "  상태: $($task.State)" -ForegroundColor White
    Write-Host "  다음 실행 시간: $((Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo).NextRunTime)" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[오류] 작업 등록 실패!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "오류 메시지: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "작업 스케줄러 설정이 완료되었습니다!" -ForegroundColor Green
Write-Host ""
pause
