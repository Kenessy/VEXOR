# VRAXION // DUAL_IGNITION_LAUNCHER v1.0
# Opens two PowerShell windows: engine + telemetry.

$workDir = "G:\AI\mirror\VRAXION"
if (-not (Test-Path $workDir)) {
    Write-Error "Project directory $workDir not found."
    return
}

Set-Location $workDir

# --- 2) ENGINE WINDOW ---
Write-Host "Launching VRAXION Engine..." -ForegroundColor Cyan
$engineCmd = @"
cd '$workDir'
`$env:TP6_RESUME="1"
`$env:TP6_SYNTH="1"
`$env:TP6_SYNTH_ONLY="1"
`$env:TP6_SEQ_MNIST="0"
`$env:TP6_OFFLINE_ONLY="1"
`$env:TP6_SYNTH_MODE="assoc_byte"
`$env:TP6_SYNTH_LEN="512"
`$env:TP6_ASSOC_KEYS="64"
`$env:TP6_ASSOC_PAIRS="4"
`$env:TP6_MAX_SAMPLES="8192"
`$env:TP6_BATCH_SIZE="152"
`$env:TP6_MAX_STEPS="999999999"
`$env:TP6_CKPT="checkpoint_last_good.pt"
`$env:TP6_UPDATE_SCALE="0.05"
`$env:TP6_SCALE_INIT="0.05"
`$env:TP6_SCALE_MIN="0.000001"
`$env:TP6_SCALE_MAX="1.0"
`$env:TP6_PTR_INERTIA_OVERRIDE="0.5"
`$env:TP6_SHARD_ADAPT="1"
`$env:TP6_SHARD_ADAPT_EVERY="1"
`$env:TP6_TRACTION_LOG="1"
`$env:TP6_SAVE_EVERY_STEPS="100"
python VRAXION_INFINITE.py
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$engineCmd"

# --- 3) TELEMETRY WINDOW ---
Write-Host "Waiting for Log Initialization..." -ForegroundColor Yellow
$logPath = Join-Path $workDir "logs\current\tournament_phase6.log"
$timeout = 60
while (-not (Test-Path $logPath) -and $timeout -gt 0) {
    Start-Sleep -Seconds 1
    $timeout -= 1
}
if (-not (Test-Path $logPath)) {
    Write-Error "Log file did not appear at $logPath"
    return
}

Write-Host "Launching Telemetry Window..." -ForegroundColor Green
$telemetryCmd = "cd '$workDir'; Get-Content '$logPath' -Wait -Tail 30"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$telemetryCmd"

Write-Host "Dual-Ignition Complete. Monitor Terminal B for progress." -ForegroundColor Green
