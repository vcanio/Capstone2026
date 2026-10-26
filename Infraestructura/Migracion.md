# Migrar Walmart a otro PC o servidor

Guía preparada para la instalación actual, revisada el 7 de octubre de 2026. Los comandos de respaldo y restauración se ejecutan cuando se decida migrar; preparar esta guía no detiene los servicios actuales.

**Alcance:** procedimiento técnico para quienes administran el laboratorio y disponen de los respaldos y la configuración privada. Para instalar la aplicación de usuario, consultar [Usar Walmart Visión](../Documentacion/Usar_Walmart_Vision.md). Los iniciadores privados del anfitrión no se distribuyen en Git ni son un requisito de Visión.

## 1. Elegir qué se traslada

| Ruta | Qué corre en el destino | Qué permanece en el PC original |
|---|---|---|
| A: usar la GPU de otro equipo | Panel, predicciones, entrenamiento y resultados. | CVAT con los usuarios, proyectos y anotaciones del equipo. |
| B: trasladar la instalación completa | Laboratorio y CVAT con su historial. | Una copia de retorno, detenida mientras se usa el destino. |

Para usar la GPU de Paulo, la ruta A es suficiente. Para reemplazar este PC por un servidor, usar la B. En ambas rutas se copian las fotos y versiones de datos: la imagen Docker contiene el entorno y el código, no los archivos de trabajo.

Los ejemplos parten de Windows en el origen (`C:\Proyectos\Walmart`) y permiten Windows o Linux en el destino. En Windows el ejemplo de destino es `D:\Proyectos\Walmart`; en Linux, `/srv/walmart`. Sustituir las rutas por las reales. La restauración completa descrita supone equipos x86_64, Linux containers y las mismas imágenes de CVAT y PostgreSQL del origen.

## 2. Preparar el destino

### 2.1. Otro PC con Windows

1. Instalar Docker Desktop y usar contenedores Linux con backend WSL2. Si se trata de Windows Server, comprobar primero el soporte de Docker Desktop para esa edición; para un servidor sin escritorio, usar la ruta Linux.
2. Actualizar el driver NVIDIA si se usará una GPU NVIDIA.
3. Abrir Docker Desktop y esperar a que el motor esté listo.
4. En PowerShell ejecutar:

```powershell
docker version
docker compose version
nvidia-smi
```

`docker version` debe mostrar cliente y servidor. `nvidia-smi` debe identificar la GPU. Si no existe una GPU NVIDIA, elegir CPU en el paso 7.

Usar Docker Compose 2.24.4 o posterior, con soporte de `!reset` y `!override` (preferiblemente una versión actual). [Compatibilidad de los ajustes Compose](https://docs.docker.com/reference/compose-file/merge/). Para GPU, revisar los [requisitos de Docker en Windows](https://docs.docker.com/desktop/features/gpu/).

### 2.2. Servidor Linux

1. Instalar Docker Engine y el complemento Docker Compose siguiendo la [guía oficial para Ubuntu](https://docs.docker.com/engine/install/ubuntu/) o la guía de la distribución del servidor.
2. Para NVIDIA, instalar el driver compatible y [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
3. Configurar Docker para NVIDIA según esa guía:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

4. Comprobar:

```bash
docker version
docker compose version
nvidia-smi
```

Si el usuario no tiene acceso a Docker, ejecutar los comandos Docker de esta guía con `sudo` o configurar ese acceso con el administrador. Usar una cuenta propietaria de `/srv/walmart`, con permiso de escritura en `Datos/Registros/Versiones_modelos`, `Laboratorio/Experimentos` y `.config-modelo`.

El laboratorio usa PyTorch 2.5.1 con CUDA 12.1. La comprobación real del paso 8 determina si esa imagen funciona con la GPU del destino. Una GPU más nueva puede necesitar actualizar coordinadamente PyTorch, torchvision y CUDA; Docker no elimina esa compatibilidad.

Reservar espacio para los archivos del proyecto, sus respaldos y las imágenes Docker. Solo la imagen de modelos ocupa aproximadamente 10 GB en esta instalación. El almacenamiento necesario crece con las fotos y los ensayos.

## 3. Preparar una copia consistente en el origen

### 3.1. Guardar el trabajo

1. Guardar las anotaciones pendientes en CVAT.
2. Esperar a que terminen entrenamientos, predicciones, importaciones y exportaciones.
3. Durante la copia, no modificar las fotos, versiones ni configuraciones.

Desde PowerShell en el PC original:

```powershell
Set-Location C:\Proyectos\Walmart
$migrationRoot = (Get-Location).Path
$migrationBackup = Join-Path $migrationRoot ('.resguardo/migracion_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $migrationBackup -ErrorAction Stop
$activeJobs = @(Invoke-RestMethod http://localhost:8090/api/jobs -TimeoutSec 10)
if (@($activeJobs | Where-Object { $_.state -eq 'running' }).Count) {
    throw 'Hay un trabajo activo. Esperar antes de copiar.'
}
docker compose -f Infraestructura/Docker/compose.modelos.yml -f Infraestructura/Docker/compose.modelos.gpu.yml stop panel_modelos
if ($LASTEXITCODE -ne 0) { throw 'No se pudo detener el panel.' }
```

Mantener esta sesión de PowerShell abierta: los pasos siguientes usan `$migrationRoot` y `$migrationBackup`. La carpeta creada contiene el paquete de migración y debe transferirse completa.

### 3.2. Solo si se mueve también CVAT: detenerlo y respaldar sus volúmenes

Para la ruta A, saltar a 3.3: CVAT sigue disponible en el origen.

Para la ruta B, avisar al equipo de la ventana de migración y ejecutar:

```powershell
$sourceCvatArgs = @(
    'compose', '--project-name', 'walmart-cvat',
    '--env-file', 'Infraestructura/CVAT/cvat.env',
    '-f', 'Laboratorio/CVAT/cvat-v2.77.0/docker-compose.yml',
    '-f', 'Infraestructura/CVAT/compose.local.yml',
    '-f', 'Infraestructura/CVAT/compose.tailscale.yml'
)
docker @sourceCvatArgs stop
if ($LASTEXITCODE -ne 0) { throw 'No se pudo detener CVAT.' }
```

Los siete volúmenes actuales son:

| Volumen | Contenido |
|---|---|
| `walmart-cvat_cvat_db` | Usuarios, proyectos, tareas, jobs y anotaciones en PostgreSQL. |
| `walmart-cvat_cvat_data` | Imágenes y archivos preparados por CVAT. |
| `walmart-cvat_cvat_keys` | Claves de Django. |
| `walmart-cvat_cvat_logs` | Logs del backend. |
| `walmart-cvat_cvat_events_db` | Datos de ClickHouse. |
| `walmart-cvat_cvat_inmem_db` | Datos persistidos de Redis. |
| `walmart-cvat_cvat_cache_db` | Datos de Kvrocks. |

El log anónimo adicional de ClickHouse no forma parte de estos siete respaldos de estado. Mantener CVAT detenido durante la copia de sus volúmenes, según la [guía de respaldo de CVAT](https://docs.cvat.ai/docs/administration/community/advanced/backup_guide/).

```powershell
$cvatVolumeNames = @(
    'walmart-cvat_cvat_db', 'walmart-cvat_cvat_data',
    'walmart-cvat_cvat_keys', 'walmart-cvat_cvat_logs',
    'walmart-cvat_cvat_events_db', 'walmart-cvat_cvat_inmem_db',
    'walmart-cvat_cvat_cache_db'
)
foreach ($migrationVolume in $cvatVolumeNames) {
    docker volume inspect $migrationVolume --format '{{.Name}}'
    if ($LASTEXITCODE -ne 0) { throw "Falta el volumen $migrationVolume" }
    docker run --rm `
        --mount "type=volume,source=$migrationVolume,target=/source,readonly" `
        --mount "type=bind,source=$migrationBackup,target=/backup" `
        alpine:3.21 tar -czf "/backup/$migrationVolume.tar.gz" -C /source .
    if ($LASTEXITCODE -ne 0) { throw "Falló el respaldo de $migrationVolume" }
}
```

Exportar también las imágenes exactas del CVAT actual para reutilizar las mismas dependencias en el destino:

```powershell
$cvatImages = @(docker ps -a --filter 'label=com.docker.compose.project=walmart-cvat' --format '{{.Image}}' | Sort-Object -Unique)
if (-not $cvatImages.Count) { throw 'No se encontraron las imágenes de CVAT.' }
docker image save -o (Join-Path $migrationBackup 'imagenes_cvat.tar') @cvatImages
if ($LASTEXITCODE -ne 0) { throw 'Falló la exportación de imágenes de CVAT.' }
```

No usar `down --volumes`, `docker volume prune` ni eliminar los volúmenes del origen. La copia original permite volver atrás.

### 3.3. Empaquetar los archivos del proyecto

Este paquete sirve para las dos rutas. Copia el código, los Compose, las fotos, inventarios, pesos, versiones, ensayos y configuraciones. Incluye los archivos ocultos requeridos y la instalación original de CVAT, aunque Git los ignore.

```powershell
$migrationArchive = Join-Path $migrationBackup 'walmart_proyecto.tar.gz'
tar -czf $migrationArchive `
    --exclude=.venv-modelo --exclude=.venv-cvat `
    --exclude=.resguardo --exclude=.git --exclude=.agents `
    --exclude=__pycache__ -C $migrationRoot .
if ($LASTEXITCODE -ne 0) { throw 'Falló el paquete de archivos del proyecto.' }
```

El paquete contiene credenciales y datos del proyecto. Transferirlo por un medio privado y conservarlo con acceso restringido. No cargarlo a un repositorio público. No hace falta copiar los entornos `.venv`: Docker proporciona el entorno de ejecución.

Para evitar construir o descargar la imagen de modelos en el destino, exportarla también:

```powershell
docker image save -o (Join-Path $migrationBackup 'imagen_modelos.tar') walmart-panel-modelos:local
if ($LASTEXITCODE -ne 0) { throw 'Falló la exportación de la imagen del laboratorio.' }
```

Crear un manifiesto de integridad para todos los archivos del paquete:

```powershell
$migrationHashes = @(Get-ChildItem -LiteralPath $migrationBackup -File | ForEach-Object {
    [pscustomobject]@{ archivo = $_.Name; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
})
$migrationHashes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $migrationBackup 'SHA256.json') -Encoding UTF8
```

**Resultado esperado:** ruta A tiene `walmart_proyecto.tar.gz`, `imagen_modelos.tar` y `SHA256.json`. Ruta B tiene además `imagenes_cvat.tar` y siete archivos `walmart-cvat_*.tar.gz`.

En la ruta A, después de copiar se puede volver a levantar el panel original con `& .\Laboratorio\Modelos\iniciar_panel.ps1`. Las copias de resultados de ambos equipos serán independientes; acordar cuál se conserva como referencia y no fusionar automáticamente carpetas de ensayos.

## 4. Transferir y comprobar el paquete

Usar un disco externo o transferencia privada. En Linux por SSH, por ejemplo, desde el PowerShell del origen:

```powershell
scp -r $migrationBackup usuario@SERVIDOR:/srv/transferencias/
```

Crear antes `/srv/transferencias` en el servidor y darle permisos a esa cuenta. `SERVIDOR` es la dirección real, IP o nombre privado de Tailscale del equipo destino; no es un nombre definido por esta guía.

### 4.1. Comprobar en Windows

Suponiendo que se copió el paquete a `D:\Transferencias\migracion_walmart`:

```powershell
$migrationBackup = (Resolve-Path D:\Transferencias\migracion_walmart).Path
$migrationHashes = Get-Content -LiteralPath (Join-Path $migrationBackup 'SHA256.json') -Raw | ConvertFrom-Json
foreach ($migrationHash in $migrationHashes) {
    $migrationFile = Join-Path $migrationBackup $migrationHash.archivo
    if ((Get-FileHash -LiteralPath $migrationFile -Algorithm SHA256).Hash -ne $migrationHash.sha256) {
        throw "La copia no coincide: $($migrationHash.archivo)"
    }
}
Write-Output 'Todos los archivos coinciden.'
```

### 4.2. Comprobar en Linux

Cambiar la ruta por la carpeta transferida:

```bash
cd /srv/transferencias/migracion_walmart
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path.cwd()
items = json.loads((root / 'SHA256.json').read_text(encoding='utf-8-sig'))
if isinstance(items, dict):
    items = [items]
for item in items:
    path = root / item['archivo']
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    assert digest.hexdigest().lower() == item['sha256'].lower(), f'La copia no coincide: {path.name}'
print('Todos los archivos coinciden.')
PY
```

Este ejemplo utiliza Python 3, sin bibliotecas adicionales. Si falla una comprobación, volver a copiar ese archivo antes de restaurar.

## 5. Extraer el proyecto en el destino

Usar una carpeta nueva, vacía, para que la restauración no mezcle dos instalaciones.

### Windows

```powershell
$migrationTarget = 'D:\Proyectos\Walmart'
if (Test-Path -LiteralPath $migrationTarget) { throw 'Elegir una carpeta nueva, vacía.' }
New-Item -ItemType Directory -Path $migrationTarget -ErrorAction Stop
tar -xzf (Join-Path $migrationBackup 'walmart_proyecto.tar.gz') -C $migrationTarget
if ($LASTEXITCODE -ne 0) { throw 'Falló la extracción.' }
Set-Location $migrationTarget
docker image load -i (Join-Path $migrationBackup 'imagen_modelos.tar')
if ($LASTEXITCODE -ne 0) { throw 'Falló la carga de la imagen.' }
```

### Linux

El administrador debe crear `/srv/walmart` vacío y hacerlo escribible para la cuenta de trabajo. Después, con esa cuenta:

```bash
set -e
test -z "$(ls -A /srv/walmart)" || { echo 'La carpeta no está vacía'; exit 1; }
tar -xzf /srv/transferencias/migracion_walmart/walmart_proyecto.tar.gz -C /srv/walmart
cd /srv/walmart
docker image load -i /srv/transferencias/migracion_walmart/imagen_modelos.tar
mkdir -p .config-modelo Laboratorio/Experimentos Datos/Registros/Versiones_modelos
```

Comprobar que están presentes:

```text
Infraestructura/Docker/compose.modelos.yml
Infraestructura/Docker/compose.modelos.gpu.yml
Infraestructura/Docker/compose.modelos.linux.yml
Laboratorio/Modelos/docker/Dockerfile
Datos/Registros/
Datos/V2/
Datos/V1/Lider/
Datos/V1/Sinteticas/
Laboratorio/Experimentos/panel_pruebas/Subidas_panel/
Datos/V1/Reservadas/
Laboratorio/Experimentos/
Modelos/preentrenados/yolo11n-seg.pt
Datos/Registros/CVAT/organizacion.json
Datos/Registros/reserva_evaluacion.json
Infraestructura/CVAT/acceso_local.json
```

Los originales, pesos y configuraciones no se recuperan con un simple `git clone`, porque algunos están ignorados por Git. El paquete anterior sí los incluye.

## 6. Elegir dónde estará CVAT

Para crear y editar la configuración del laboratorio, desde la raíz del destino:

**Windows:**

```powershell
Copy-Item -LiteralPath Infraestructura/Docker/.env.modelos.example -Destination Infraestructura/Docker/.env.modelos
notepad Infraestructura/Docker/.env.modelos
```

**Linux:**

```bash
cp Infraestructura/Docker/.env.modelos.example Infraestructura/Docker/.env.modelos
nano Infraestructura/Docker/.env.modelos
```

Usar otro editor si no está instalado Nano. Guardar en ese archivo los valores de la ruta A o B que se indican a continuación.

### 6.A. CVAT continúa en el PC original

1. Mantener el PC original encendido con Docker y Tailscale conectados.
2. Instalar Tailscale en el destino y autorizar ese equipo para acceder al CVAT del proyecto en la política de la red.
3. Comprobar desde el destino que se puede abrir `https://TU_HOST_CVAT` e iniciar sesión con la cuenta autorizada.
4. Crear o editar `Infraestructura/Docker/.env.modelos` en la carpeta Infraestructura/Docker del proyecto destino:

```dotenv
MODEL_CVAT_URL=https://TU_HOST_CVAT
MODEL_CVAT_HOST_HEADER=
```

El valor vacío de `MODEL_CVAT_HOST_HEADER` es intencional: la petición debe usar el dominio HTTPS real.

5. En `Infraestructura/CVAT/acceso_local.json`, usar la cuenta autorizada para leer los jobs del proyecto. El formato requerido es:

```json
{
  "username": "USUARIO_AUTORIZADO",
  "password": "CONTRASENA_DE_ESTA_CUENTA"
}
```

No usar esos textos de ejemplo como credenciales. El archivo se monta de solo lectura y no se incorpora a la imagen.

6. Continuar en el paso 7. No restaurar volúmenes de CVAT ni ejecutar los scripts de inicio local de CVAT en el destino.

El entrenamiento sobre copias ya revisadas puede funcionar sin consultar CVAT en ese momento. Importar nuevas anotaciones sí requiere la conexión y permisos de esa cuenta.

**Limitación actual de la interfaz:** los enlaces «Abrir trabajo en CVAT» todavía apuntan a `http://localhost:8082`. Cambiar `Infraestructura/Docker/.env.modelos` configura el importador, no esos enlaces. En la ruta A, abrir CVAT por su URL privada directamente y localizar el job indicado. Para adaptar los enlaces automáticamente habría que hacer otro cambio de interfaz.

### 6.B. CVAT también se traslada

El respaldo de volúmenes mantiene los IDs de proyectos, tareas y jobs. Crear una instalación vacía y reimportar proyectos por la interfaz puede cambiar esos IDs y requerir adaptar el laboratorio. Esta guía restaura los volúmenes completos.

#### 6.B.1. Preparar el Compose del destino

Copiar `Infraestructura/Docker/.env.cvat.migracion.example` a `Infraestructura/Docker/.env.cvat.migracion` y editarlo. En Windows:

```powershell
Copy-Item -LiteralPath Infraestructura/Docker/.env.cvat.migracion.example -Destination Infraestructura/Docker/.env.cvat.migracion
notepad Infraestructura/Docker/.env.cvat.migracion
```

En Linux:

```bash
cp Infraestructura/Docker/.env.cvat.migracion.example Infraestructura/Docker/.env.cvat.migracion
nano Infraestructura/Docker/.env.cvat.migracion
```

Contenido para el ejemplo de Windows:

```dotenv
CVAT_VERSION=v2.77.0
CVAT_HOST=localhost
CVAT_DOMAIN=localhost
WALMART_IMAGE_DIR=D:/Proyectos/Walmart/Datos/V1/Lider
CVAT_PROXY_TRUSTED_IPS=127.0.0.1/32
```

En Linux usar `WALMART_IMAGE_DIR=/srv/walmart/Datos/V1/Lider`.

La versión debe coincidir con la del respaldo. Restaurar primero y actualizar CVAT después, en otra operación, según la [guía oficial de restauración](https://docs.cvat.ai/docs/administration/community/advanced/backup_guide/).

Definir los argumentos de CVAT en el destino. **Windows, PowerShell:**

```powershell
$targetCvatArgs = @(
    'compose', '--project-name', 'walmart-cvat',
    '--env-file', 'Infraestructura/Docker/.env.cvat.migracion',
    '-f', 'Laboratorio/CVAT/cvat-v2.77.0/docker-compose.yml',
    '-f', 'Infraestructura/CVAT/compose.local.yml',
    '-f', 'Infraestructura/Docker/compose.cvat.migracion.yml'
)
docker @targetCvatArgs config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Configuración de CVAT inválida.' }
docker image load -i (Join-Path $migrationBackup 'imagenes_cvat.tar')
if ($LASTEXITCODE -ne 0) { throw 'Falló la carga de imágenes de CVAT.' }
```

**Linux, Bash:** mantener esta terminal para los pasos siguientes.

```bash
set -e
target_cvat_args=(compose --project-name walmart-cvat --env-file Infraestructura/Docker/.env.cvat.migracion
  -f Laboratorio/CVAT/cvat-v2.77.0/docker-compose.yml
  -f Infraestructura/CVAT/compose.local.yml
  -f Infraestructura/Docker/compose.cvat.migracion.yml)
docker "${target_cvat_args[@]}" config --quiet
docker image load -i /srv/transferencias/migracion_walmart/imagenes_cvat.tar
```

El último archivo reemplaza las tres rutas de imágenes de Windows por la ruta configurada. No incluir `compose.tailscale.yml` del origen: contiene su dominio y direcciones de proxy específicos. Los iniciadores privados del origen validan la identidad de ese PC y no sirven para autorizar una máquina nueva; no se distribuyen en el repositorio público.

#### 6.B.2. Restaurar los siete volúmenes antes de iniciar CVAT

Este procedimiento requiere un destino donde no exista todavía el proyecto `walmart-cvat`. Si ya existen sus volúmenes, hacer un respaldo de esa instalación y resolver la convivencia antes de seguir; los comandos se detienen para evitar sobrescribirlos.

**Windows, PowerShell:**

```powershell
$cvatVolumeNames = @(
    'walmart-cvat_cvat_db', 'walmart-cvat_cvat_data',
    'walmart-cvat_cvat_keys', 'walmart-cvat_cvat_logs',
    'walmart-cvat_cvat_events_db', 'walmart-cvat_cvat_inmem_db',
    'walmart-cvat_cvat_cache_db'
)
foreach ($migrationVolume in $cvatVolumeNames) {
    docker volume inspect $migrationVolume 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { throw "Ya existe $migrationVolume; no sobrescribir." }
    if (-not (Test-Path -LiteralPath (Join-Path $migrationBackup "$migrationVolume.tar.gz"))) {
        throw "Falta el respaldo de $migrationVolume"
    }
}
foreach ($migrationVolume in $cvatVolumeNames) {
    docker volume create --label 'com.docker.compose.project=walmart-cvat' `
        --label "com.docker.compose.volume=$($migrationVolume.Substring('walmart-cvat_'.Length))" $migrationVolume
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear $migrationVolume" }
    docker run --rm `
        --mount "type=volume,source=$migrationVolume,target=/restore" `
        --mount "type=bind,source=$migrationBackup,target=/backup,readonly" `
        alpine:3.21 sh -c 'if [ -n "$(ls -A /restore)" ]; then echo "Volumen no vacio"; exit 12; fi; tar -xzf "/backup/$1.tar.gz" -C /restore' sh $migrationVolume
    if ($LASTEXITCODE -ne 0) { throw "Falló la restauración de $migrationVolume" }
}
```

**Linux, Bash:**

```bash
set -e
migration_backup=/srv/transferencias/migracion_walmart
cvat_volume_names=(walmart-cvat_cvat_db walmart-cvat_cvat_data
  walmart-cvat_cvat_keys walmart-cvat_cvat_logs walmart-cvat_cvat_events_db
  walmart-cvat_cvat_inmem_db walmart-cvat_cvat_cache_db)
for migration_volume in "${cvat_volume_names[@]}"; do
  if docker volume inspect "$migration_volume" >/dev/null 2>&1; then
    echo "Ya existe $migration_volume; no sobrescribir" >&2
    exit 1
  fi
  test -f "$migration_backup/$migration_volume.tar.gz"
done
for migration_volume in "${cvat_volume_names[@]}"; do
  docker volume create --label com.docker.compose.project=walmart-cvat \
    --label "com.docker.compose.volume=${migration_volume#walmart-cvat_}" "$migration_volume"
  docker run --rm \
    --mount "type=volume,source=$migration_volume,target=/restore" \
    --mount "type=bind,source=$migration_backup,target=/backup,readonly" \
    alpine:3.21 sh -c 'if [ -n "$(ls -A /restore)" ]; then echo "Volumen no vacio"; exit 12; fi; tar -xzf "/backup/$1.tar.gz" -C /restore' sh "$migration_volume"
done
```

Los archivos se restauran mediante un contenedor para conservar permisos internos de Linux. No copiarlos directamente a carpetas de Windows como sustituto de los volúmenes. [Respaldo y restauración de volúmenes Docker](https://docs.docker.com/engine/storage/volumes/).

#### 6.B.3. Iniciar y revisar CVAT

**Windows:**

```powershell
docker @targetCvatArgs up -d
if ($LASTEXITCODE -ne 0) { throw 'CVAT no pudo iniciar.' }
docker @targetCvatArgs ps
```

**Linux:**

```bash
docker "${target_cvat_args[@]}" up -d
docker "${target_cvat_args[@]}" ps
```

Esperar a que el backend esté listo y abrir `http://localhost:8082` en el destino. En un servidor usar el túnel del paso 9. Iniciar sesión con una cuenta existente y comprobar:

1. Proyecto `Walmart Stock`, ID 4.
2. Tarea Piloto, ID 13, jobs 27, 28 y 29.
3. Tarea del set completo, ID 14, jobs 30, 31 y 32.
4. Una foto real y sus polígonos guardados, además de los usuarios y asignaciones.

Estas referencias corresponden a la organización actual; si cambia antes de migrar, anotar las referencias vigentes al hacer el respaldo. Si aparece CVAT vacío, detenerse y revisar que Compose haya montado los volúmenes restaurados.

Configurar `Infraestructura/Docker/.env.modelos` para el CVAT del mismo equipo. **Windows:**

```dotenv
MODEL_CVAT_URL=http://host.docker.internal:8082/api
MODEL_CVAT_HOST_HEADER=localhost:8082
```

**Linux, con el ajuste de red del paso 7:**

```dotenv
MODEL_CVAT_URL=http://127.0.0.1:8082/api
MODEL_CVAT_HOST_HEADER=localhost:8082
```

#### 6.B.4. Opcional: dar acceso privado al CVAT nuevo

Después de comprobar la restauración local:

1. Instalar/conectar Tailscale en el destino y obtener su nuevo dominio de equipo. No asumir que conservará `pcvicen.tailca514b.ts.net`.
2. Autorizar a los integrantes para acceder al nuevo equipo y puerto HTTPS en la política de la red.
3. Cambiar `CVAT_DOMAIN` en `Infraestructura/Docker/.env.cvat.migracion` por ese dominio, sin `https://` ni rutas.
4. Consultar la dirección del gateway de la red Docker:

```text
docker inspect walmart_traefik --format '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}'
```

5. Usar ese valor en `CVAT_PROXY_TRUSTED_IPS`, por ejemplo `127.0.0.1/32,172.20.0.1/32` **solo si** el gateway observado es `172.20.0.1`. Volver a ejecutar `up -d` con los argumentos de destino para aplicar los cambios.
6. Comprobar `tailscale serve status` en ese equipo antes de agregar el servicio. Si no hay otro servicio en HTTPS 443, ejecutar:

**Windows:**

```powershell
& "$env:ProgramFiles\Tailscale\tailscale.exe" serve --bg --https=443 http://127.0.0.1:8082
```

**Linux:**

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:8082
```

7. Comprobar acceso, login y guardado de una anotación desde otro equipo autorizado. Actualizar los enlaces de la documentación y los equipos que importaban anotaciones del origen.

Usar [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve) para el acceso privado. No reutilizar `estado_tailscale.json` como prueba de que la política de la máquina nueva está verificada. Ese archivo describe el PC original.

## 7. Iniciar el laboratorio en el destino

### 7.1. Windows con GPU NVIDIA

```powershell
Set-Location D:\Proyectos\Walmart
$targetModelArgs = @('compose', '--env-file', 'Infraestructura/Docker/.env.modelos', '-f', 'Infraestructura/Docker/compose.modelos.yml', '-f', 'Infraestructura/Docker/compose.modelos.gpu.yml')
docker @targetModelArgs config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Configuración del laboratorio inválida.' }
docker @targetModelArgs up -d --wait --wait-timeout 120
if ($LASTEXITCODE -ne 0) { throw 'El laboratorio no pudo iniciar.' }
```

La imagen se cargó en el paso 5. Si se eligió no exportarla, añadir `--build` a `up`; la primera construcción descarga varios GB. El script `iniciar_panel.ps1` carga `Infraestructura/Docker/.env.modelos` automáticamente y también admite `-Build`.

### 7.2. Windows sin GPU NVIDIA

Usar la misma secuencia, pero definir:

```powershell
$targetModelArgs = @('compose', '--env-file', 'Infraestructura/Docker/.env.modelos', '-f', 'Infraestructura/Docker/compose.modelos.yml')
docker @targetModelArgs up -d --wait --wait-timeout 120
```

El panel y los modelos usan CPU. No ejecutar después `iniciar_cvat.ps1` en el destino, porque ese script del origen inicia el panel con GPU por defecto. Usar los argumentos de destino de esta guía para administrar ambos proyectos.

### 7.3. Linux con GPU NVIDIA

```bash
set -e
cd /srv/walmart
target_model_args=(compose --env-file Infraestructura/Docker/.env.modelos
  -f Infraestructura/Docker/compose.modelos.yml -f Infraestructura/Docker/compose.modelos.gpu.yml -f Infraestructura/Docker/compose.modelos.linux.yml)
docker "${target_model_args[@]}" config --quiet
docker "${target_model_args[@]}" up -d --wait --wait-timeout 120
```

### 7.4. Linux sin GPU NVIDIA

```bash
set -e
cd /srv/walmart
target_model_args=(compose --env-file Infraestructura/Docker/.env.modelos
  -f Infraestructura/Docker/compose.modelos.yml -f Infraestructura/Docker/compose.modelos.linux.yml)
docker "${target_model_args[@]}" up -d --wait --wait-timeout 120
```

`Infraestructura/Docker/compose.modelos.linux.yml` usa la red del anfitrión y mantiene el panel escuchando en `127.0.0.1`. Así puede alcanzar CVAT local y la red Tailscale del servidor sin publicar el panel en Internet. Este ajuste está preparado para Docker Engine en Linux; en Windows seguir los comandos específicos anteriores. [Red del anfitrión en Docker](https://docs.docker.com/engine/network/drivers/host/).

## 8. Comprobar la migración

Ejecutar los siguientes comandos con el prefijo definido en el paso 7: en PowerShell `docker @targetModelArgs`; en Bash `docker "${target_model_args[@]}"`.

### 8.1. Estado y GPU

Ejemplo PowerShell; en Bash cambiar solo el prefijo:

```powershell
docker @targetModelArgs ps
docker @targetModelArgs exec -T panel_modelos python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Dispositivo:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'); print('Tensor:', torch.ones(4, device='cuda' if torch.cuda.is_available() else 'cpu').sum().item())"
```

El panel debe estar `healthy`. En la ruta GPU debe aparecer `CUDA: True`, la GPU del destino y `Tensor: 4.0`. Si se esperaba GPU y aparece CPU o el tensor falla, corregir esa configuración antes de entrenar.

### 8.2. Datos y conexión a CVAT desde el contenedor

```powershell
docker @targetModelArgs exec -T panel_modelos python -c "import sys; sys.path.insert(0, '/app/Herramientas/Modelos'); import panel_modelos as p, datos_modelos as d; print('Catalogo:', {k:len(v) for k,v in p.catalog().items()}); print('Proyecto CVAT:', d.CvatReader().request('/projects/4')['name'])"
```

Se esperan las fotos de desarrollo, versiones y modelos copiados y el proyecto `Walmart Stock`. La cuenta puede necesitar permisos para leer ese proyecto. Este comando comprueba la conexión **desde el contenedor**: abrir CVAT en el navegador del anfitrión no comprueba por sí solo DNS y acceso desde Docker.

### 8.3. Recorrido de la interfaz

1. Abrir `http://localhost:8090`.
2. Verificar las copias en Preparar datos y las versiones de revisión.
3. Probar una foto de desarrollo con un peso existente; confirmar que aparece la predicción y no un error de rutas.
4. Consultar los ensayos y comparaciones que se hayan copiado.
5. Si se necesita comprobar entrenamiento, crear un ensayo nuevo de una época, con tamaño 320 y batch 1, usando una versión revisada. Nombrarlo como prueba técnica y conservarlo separado de los ensayos usados para comparar modelos. Confirmar que se guardan pesos, métricas y comparaciones.

Los `data.yaml` y algunos `args.yaml` de ensayos históricos pueden contener rutas del equipo original. El panel puede consultar el historial y genera rutas nuevas al preparar un ensayo nuevo; volver a evaluar directamente un ensayo viejo con CLI puede requerir adaptar su `data.yaml`. No sobrescribir el historial original para hacer esa prueba.

### 8.4. Persistencia y arranque automático

Después de terminar cualquier trabajo:

```powershell
docker @targetModelArgs restart panel_modelos
docker @targetModelArgs up -d --wait --wait-timeout 120
```

Volver a abrir el panel y confirmar que siguen las copias y resultados. En Windows, cerrar y abrir Docker Desktop en una ventana sin trabajos activos; en Linux, el administrador puede reiniciar Docker en esa misma condición. CVAT y el panel tienen política `restart: always` y deben volver a iniciar. En Linux configurar Docker para arrancar al iniciar el sistema según la distribución.

El reinicio inicia los servicios; no reanuda entrenamientos interrumpidos ni abre automáticamente el navegador.

## 9. Abrir el panel de un servidor desde otro computador

El panel actual valida `Host` y `Origin` locales. Para usarlo en un servidor sin modificar esa protección, usar un túnel SSH. Desde tu computador:

```powershell
ssh -N -L 8090:127.0.0.1:8090 -L 8082:127.0.0.1:8082 usuario@SERVIDOR
```

Mantener la terminal abierta y entrar en el navegador a:

- `http://localhost:8090`: panel del servidor.
- `http://localhost:8082`: CVAT del servidor, si se siguió la ruta B.

El destino necesita SSH configurado y autorizado. Se puede usar su dirección privada de Tailscale como `SERVIDOR`. En la ruta A, reenviar solo 8090 y abrir CVAT por la URL del PC original.

Los puertos 8090 y 8082 de tu computador deben estar libres. Si todavía ejecuta la instalación anterior, esperar a que terminen sus trabajos y detener los servicios locales antes de crear el túnel. Mantener esos mismos puertos locales conserva la validación del panel y los enlaces actuales a CVAT.

No cambiar la publicación del panel a `0.0.0.0` ni agregarlo directamente a Serve como sustituto del túnel: compartirlo por dominio remoto requiere adaptar explícitamente la validación y sus permisos.

## 10. Cambiar el equipo de referencia o volver al origen

### Si la migración funcionó

1. En la ruta B, mantener CVAT del origen detenido para que el equipo no anote en dos bases independientes.
2. Comunicar la URL del nuevo CVAT y actualizar README y enlaces del proyecto.
3. Conservar el paquete de respaldo y la instalación anterior hasta comprobar el uso real del nuevo destino.
4. Programar los respaldos del nuevo equipo. Docker facilita recrear el entorno; los archivos y volúmenes necesitan su propio respaldo.

### Si falla antes de empezar a trabajar en el destino

1. Detener el laboratorio del destino con su prefijo del paso 7 y `stop`.
2. Si se siguió la ruta B, detener CVAT del destino con sus argumentos de 6.B.1 y `stop`.
3. En el origen, con sus fuentes CVAT, archivos privados y volúmenes originales conservados, ejecutar desde `C:\Proyectos\Walmart`:

```powershell
& .\Laboratorio\CVAT\iniciar_cvat.ps1
```

Ese script vuelve a levantar CVAT y el panel con la configuración local conservada; no configura el acceso privado de Tailscale. El administrador debe comprobar también el acceso privado con la configuración verificada del origen antes de reanudar el trabajo compartido. En la ruta A, basta `& .\Laboratorio\Modelos\iniciar_panel.ps1`.

Si ya se guardaron anotaciones o resultados nuevos en el destino, respaldarlos antes de volver: el origen conserva el estado del momento de la copia, no los cambios posteriores. No unir bases de datos ni carpetas de ensayos sobreescribiendo archivos.

## 11. Problemas frecuentes

| Síntoma | Comprobación y acción |
|---|---|
| Docker no muestra la sección Server | Iniciar Docker y comprobar permisos del usuario. |
| `bind source path does not exist` | Revisar la extracción y `WALMART_IMAGE_DIR`; no reemplazar datos faltantes por carpetas vacías. |
| El panel permanece unhealthy | Consultar `logs --tail 80 panel_modelos` con los mismos archivos Compose y `.env` usados para iniciarlo. |
| No hay GPU o error de CUDA | Verificar driver, backend WSL2 o Container Toolkit, archivo GPU y compatibilidad de la imagen con esa GPU. |
| CVAT no conecta desde el contenedor | Revisar `Infraestructura/Docker/.env.modelos`, Tailscale, permisos y la prueba 8.2; en Linux incluir el ajuste de red. |
| CVAT devuelve 401/403 al importar | Revisar cuenta y permisos sobre los jobs, sin publicar las credenciales. |
| CVAT abre sin tareas | Comprobar que usa `walmart-cvat_*` restaurados y el proyecto Compose `walmart-cvat`. |
| «Abrir trabajo en CVAT» abre el PC equivocado | En ruta A los enlaces aún son locales; abrir la URL privada del CVAT original. En servidor completo usar el túnel de ambos puertos. |
| Guardar por HTTPS falla por origen/CSRF | Revisar el dominio del destino y los encabezados del proxy, especialmente el gateway autorizado. |
| Puerto 8090 ocupado | Detener el panel manual o la instalación local anterior después de confirmar que no hay un trabajo activo. |
| Faltan ensayos/modelos | Comprobar copia de `Laboratorio/Experimentos` y `Modelos`; la imagen Docker no incluye esos datos. |

Los comandos de Compose de los ajustes de destino se validaron en el equipo actual. La restauración real y el funcionamiento del hardware de otro equipo se verifican durante la migración con los pasos 6 a 8.
