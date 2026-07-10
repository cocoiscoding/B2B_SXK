# Test which ports are available for Vite binding
Write-Host ""
Write-Host "=== Port Availability Check ===" -ForegroundColor Cyan
Write-Host ""

$candidatePorts = @(52700, 52701, 52702, 52703, 52710, 52720, 52730, 52750, 52780, 52800, 52888, 52900, 53200, 53500)

foreach ($port in $candidatePorts) {
  $tcp = New-Object System.Net.Sockets.TcpClient
  try {
    $tcp.Connect("127.0.0.1", $port)
    Write-Host ("  [BUSY] 127.0.0.1:{0,-5} - in use" -f $port) -ForegroundColor Red
    $tcp.Close()
  } catch {
    Write-Host ("  [FREE] 127.0.0.1:{0,-5} - available" -f $port) -ForegroundColor Green
  }
}

Write-Host ""
Write-Host "Tip: Change VITE_PORT to the first [FREE] port" -ForegroundColor Yellow
Write-Host ""