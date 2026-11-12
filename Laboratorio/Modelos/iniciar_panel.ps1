param([switch]$Cpu, [switch]$Build, [switch]$Dev, [switch]$ConCvat)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$panelDockerRoot = Join-Path $projectRoot 'Infraestructura/Docker'
$panelComposeArgs = @('compose', '--project-name', 'walmart-modelos', '-f', (Join-Path $panelDockerRoot 'compose.modelos.yml'))
$panelEnvPath = Join-Path $panelDockerRoot '.env.modelos'
if (Test-Path -LiteralPath $panelEnvPath) { $panelComposeArgs += @('--env-file', $panelEnvPath) }
if (-not $Cpu) { $panelComposeArgs += @('-f', (Join-Path $panelDockerRoot 'compose.modelos.gpu.yml')) }
if ($Dev) { $panelComposeArgs += @('-f', (Join-Path $panelDockerRoot 'compose.modelos.dev.yml')) }
if ($ConCvat) { $panelComposeArgs += @('-f', (Join-Path $panelDockerRoot 'compose.modelos.cvat.yml')) }
$storageConfig = Join-Path $projectRoot '.config-modelo/almacenamiento.local.json'
if (-not $env:WALMART_DATA_ROOT -and (Test-Path -LiteralPath $storageConfig)) {
    $env:WALMART_DATA_ROOT = (Get-Content -LiteralPath $storageConfig -Raw -Encoding UTF8 | ConvertFrom-Json).data_root
}
if ($env:WALMART_DATA_ROOT) {
    if (-not (Test-Path -LiteralPath $env:WALMART_DATA_ROOT -PathType Container)) { throw 'Datasets no disponibles: conecta WALMART_DATA_ROOT antes de iniciar el laboratorio.' }
    $panelComposeArgs += @('-f', (Join-Path $panelDockerRoot 'compose.modelos.datos.yml'))
}
$panelComposeArgs += @('up', '-d', '--wait', '--wait-timeout', '90')
if ($Build) { $panelComposeArgs += '--build' }
& docker @panelComposeArgs
if ($LASTEXITCODE -ne 0) { throw 'El panel no pudo arrancar. Comprueba Docker, el puerto 8090 y el acceso a la GPU.' }
Write-Output 'Panel de modelos: http://localhost:8090'
