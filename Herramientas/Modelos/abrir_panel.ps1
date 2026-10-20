$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$panelUrl = 'http://localhost:8090'
$panelProbeUrl = 'http://127.0.0.1:8090/api/health'
$panelReady = $false
try {
    $response = Invoke-RestMethod $panelProbeUrl -TimeoutSec 2
    $panelReady = $response.status -eq 'ok'
} catch { }
if (-not $panelReady) {
    & (Join-Path $PSScriptRoot 'iniciar_panel.ps1')
    $response = Invoke-RestMethod $panelProbeUrl -TimeoutSec 10
    $panelReady = $response.status -eq 'ok'
}
if (-not $panelReady) { throw 'No se pudo iniciar el panel en el puerto 8090.' }
Start-Process $panelUrl
