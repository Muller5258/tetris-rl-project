Write-Host "Stopping demo processes..." -ForegroundColor Cyan

# Kill vite node processes that were started from this repo (best effort)
Get-Process node -ErrorAction SilentlyContinue | Where-Object {
  $_.Path -like "*node.exe*"
} | ForEach-Object {
  try { $_.Kill() } catch {}
}

# Kill python running watch_ppo_ws.py (best effort)
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match "watch_ppo_ws\.py"
} | ForEach-Object {
  try { Stop-Process -Id $_.ProcessId -Force } catch {}
}

Write-Host "Done." -ForegroundColor Green
