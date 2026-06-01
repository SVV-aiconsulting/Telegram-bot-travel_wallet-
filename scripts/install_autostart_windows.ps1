# Регистрирует задачу в Планировщике Windows: бот стартует после перезагрузки ПК/сервера.
# Запускайте PowerShell от имени администратора:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\scripts\install_autostart_windows.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RunScript = Join-Path $ProjectRoot "scripts\run_bot.ps1"
$TaskName = "TravelWalletTelegramBot"

if (-not (Test-Path $RunScript)) {
    Write-Error "Не найден $RunScript"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunScript`"" `
    -WorkingDirectory $ProjectRoot

# Запуск при старте системы (через 1 мин — чтобы поднялась сеть)
$trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay (New-TimeSpan -Minutes 1)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Telegram-бот миникошелёк путешественника (автозапуск после перезагрузки)" `
    -Force | Out-Null

Write-Host "Готово. Задача '$TaskName' создана (запуск при старте Windows)."
Write-Host "Проверка: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "Ручной старт: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Удаление:   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
