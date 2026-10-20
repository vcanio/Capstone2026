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
$panelComposeArgs += @('up', '-d', '--wait', '--wait-timeout', '90')
if ($Build) { $panelComposeArgs += '--build' }
& docker @panelComposeArgs
if ($LASTEXITCODE -ne 0) { throw 'El panel no pudo arrancar. Comprueba Docker, el puerto 8090 y el acceso a la GPU.' }
Write-Output 'Panel de modelos: http://localhost:8090'
