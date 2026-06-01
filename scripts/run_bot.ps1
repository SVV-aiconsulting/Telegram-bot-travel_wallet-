# Запуск бота с автоперезапуском при падении процесса.
# Используется вручную или из Планировщика заданий Windows после перезагрузки ПК/сервера.

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$MainScript = Join-Path $ProjectRoot "main.py"
$LogDir = Join-Path $ProjectRoot "logs"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Set-Location $ProjectRoot

if (-not (Test-Path $PythonExe)) {
    Write-Error "Не найден venv: $PythonExe. Создайте: python -m venv venv; pip install -r requirements.txt"
}

if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    Write-Error "Не найден файл .env в $ProjectRoot"
}

function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $logFile = Join-Path $LogDir "bot.log"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

Write-Log "Старт обёртки run_bot.ps1 (каталог: $ProjectRoot)"

# При перезагрузке сервера Планировщик снова запустит этот скрипт.
# Если main.py упадёт — подождём и перезапустим (сеть, Telegram API).
$restartDelaySeconds = 10

while ($true) {
    Write-Log "Запуск: $PythonExe $MainScript"
    try {
        & $PythonExe $MainScript 2>&1 | ForEach-Object {
            Write-Log $_
        }
        $exitCode = $LASTEXITCODE
    }
    catch {
        Write-Log "Ошибка запуска: $_"
        $exitCode = 1
    }

    if ($exitCode -eq 0) {
        Write-Log "main.py завершился с кодом 0 (штатный выход). Остановка цикла."
        break
    }

    Write-Log "main.py завершился с кодом $exitCode. Повтор через $restartDelaySeconds с..."
    Start-Sleep -Seconds $restartDelaySeconds
}
