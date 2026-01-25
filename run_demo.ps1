param(
  [int]$FrontendPort = 5173,
  [int]$WsPort = 8765
)

$ErrorActionPreference = "Stop"

# Resolve repo root even if script is run from elsewhere
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== Tetris RL Demo Runner ==" -ForegroundColor Cyan
Write-Host "Root: $ROOT"
Write-Host ""

# --- BACKEND ---
$backendDir = Join-Path $ROOT "backend"
$venvPython = Join-Path $ROOT ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  Write-Host "ERROR: venv python not found at $venvPython" -ForegroundColor Red
  Write-Host "Did you create the venv at repo root (.venv)?" -ForegroundColor Yellow
  exit 1
}

Write-Host "Starting backend WS server..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd `"$backendDir`"; `"$venvPython`" watch_ppo_ws.py"
) | Out-Null

Start-Sleep -Milliseconds 400

# --- FRONTEND ---
$frontendDir = Join-Path $ROOT "frontend"
if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
  Write-Host "ERROR: frontend/package.json not found. Wrong folder structure?" -ForegroundColor Red
  exit 1
}

Write-Host "Starting frontend (Vite dev server)..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd `"$frontendDir`"; npm run dev"
) | Out-Null

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
Write-Host ("Frontend:  http://localhost:{0}/" -f $FrontendPort) -ForegroundColor White
Write-Host ("WebSocket: ws://localhost:{0}" -f $WsPort) -ForegroundColor White
Write-Host ""
Write-Host "If you want to stop everything: close the two new PowerShell windows." -ForegroundColor DarkGray
