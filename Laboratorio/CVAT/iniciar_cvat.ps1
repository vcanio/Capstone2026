$ErrorActionPreference = 'Stop'
$cvatRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$cvatBase = Join-Path $PSScriptRoot 'cvat-v2.77.0/docker-compose.yml'
$cvatRuntime = Join-Path $cvatRoot 'Infraestructura/CVAT'
$cvatOverride = Join-Path $cvatRuntime 'compose.local.yml'
$cvatEnv = Join-Path $cvatRuntime 'cvat.env'
$cvatComposeArgs = @('compose', '--progress', 'plain', '--project-name', 'walmart-cvat', '--env-file', $cvatEnv, '-f', $cvatBase, '-f', $cvatOverride)
$cvatPrivateOverride = Join-Path $cvatRuntime 'compose.tailscale.yml'
if (Test-Path -LiteralPath $cvatPrivateOverride) { $cvatComposeArgs += @('-f', $cvatPrivateOverride) }
& docker @cvatComposeArgs up -d cvat_server cvat_ui cvat_worker_import cvat_worker_export cvat_worker_chunks cvat_worker_utils cvat_vector traefik
if ($LASTEXITCODE -ne 0) { throw 'CVAT no pudo arrancar; revisar la salida de Docker.' }
Write-Output 'CVAT: http://localhost:8082'
& (Join-Path $cvatRoot 'Laboratorio/Modelos/iniciar_panel.ps1') -ConCvat
