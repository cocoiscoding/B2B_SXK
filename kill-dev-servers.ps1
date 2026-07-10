# ============================================================
# 神行库 · 一键清理所有占用 Vite 端口的残留进程
# 用法：在项目根目录执行 `powershell -NoProfile -ExecutionPolicy Bypass -File kill-dev-servers.ps1`
# ============================================================

Write-Host ""
Write-Host "=== 神行库 · 清理 Vite/Node 残留进程 ===" -ForegroundColor Cyan
Write-Host ""

# 1) 清理占用 Vite 默认端口的所有进程（52400-52800 范围）
$ports = @(52400, 52401, 52402, 52500, 52600, 52700, 52701, 52702, 52703, 52704, 52705)
$cleared = $false

foreach ($port in $ports) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
      Write-Host ("  [KILL] 端口 {0} 被 PID {1} ({2}) 占用 -> 结束进程" -f $port, $proc.Id, $proc.ProcessName) -ForegroundColor Yellow
      Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
      $cleared = $true
    }
  }
}

# 2) 清理所有残留的 node.exe（开发服务器），不影响其他 Node 应用
$nodeProcs = Get-Process -Name node -ErrorAction SilentlyContinue
foreach ($p in $nodeProcs) {
  $cmdline = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $p.Id) -ErrorAction SilentlyContinue).CommandLine
  if ($cmdline -and ($cmdline -match 'vite' -or $cmdline -match 'esbuild' -or $cmdline -match 'rolldown')) {
    $preview = $cmdline.Substring(0, [Math]::Min(80, $cmdline.Length))
    Write-Host ("  [KILL] 残留 node 进程 PID {0}: {1}..." -f $p.Id, $preview) -ForegroundColor Yellow
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    $cleared = $true
  }
}

if (-not $cleared) {
  Write-Host "  [OK] 没有发现残留进程" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 清理完成，现在可以重新 npm run dev ===" -ForegroundColor Cyan
Write-Host ""