# Comprobación funcional de Walmart Visión

Pauta al 21/11/2026 para un clon público final (`v2.3`). Parte de la [instalación del README](../README.md#instalación-manual-y-configuración). Los comandos se ejecutan desde la raíz con Python 3.12 y el entorno activo. No requieren entrenamiento ni acceso a CVAT.

## 1. Integridad y configuración, sin fotografías

```bash
python -m pip check
python Distribucion/verificar.py
python Aplicacion/app.py --check
python Aplicacion_Cliente/app_cliente.py --check
python Entrenamiento/preparar_datos_cvat.py --self-check
python Entrenamiento/entrenar_yolo26n_seg.py --dry-run
python Entrenamiento/evaluar_ohiggins3.py --verify-receipt
```

Resultados esperados: `pip check` informa que no hay dependencias incompatibles; el verificador devuelve `estado: correcto`, verifica los 30 archivos académicos (13 de Fase 1 intactos y 17 de Fase 2) y coteja el SHA-256 del peso oficial. El `--check` de equipo informa `Listo: 1 modelos` y versiones de PyTorch/Ultralytics; el de cliente devuelve `status: ok` y `models: 1`. Los tres scripts terminan sin error; `--dry-run` imprime parámetros sin entrenar y `--verify-receipt` devuelve `mode: verify_receipt`, cotejando el recibo y la identidad del peso. No se ejecuta inferencia sobre las 68 fotos ni se acredita la precisión actual con estas órdenes.

## 2. Pruebas automáticas existentes

En PowerShell:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='Aplicacion;Aplicacion_Cliente'
python -m unittest discover -s Aplicacion/Pruebas -v
python -m unittest discover -s Aplicacion_Cliente/Pruebas -v
python -m unittest discover -s Distribucion/tests -v
```

En Windows, `PYTHONUTF8=1` permite que las pruebas que leen texto sin codificación explícita interpreten correctamente los archivos UTF-8. Las pruebas HTTP deben poder abrir sockets locales.

En Linux/macOS:

```bash
PYTHONPATH=Aplicacion python -m unittest discover -s Aplicacion/Pruebas -v
PYTHONPATH=Aplicacion:Aplicacion_Cliente python -m unittest discover -s Aplicacion_Cliente/Pruebas -v
python -m unittest discover -s Distribucion/tests -v
```

Resultado esperado: suites terminan con `OK`. Las pruebas que necesitan activos internos ausentes o herramientas opcionales pueden omitirse; revisar cada `skipped` antes de afirmar cobertura completa. El [workflow de CI](../.github/workflows/comprobar.yml) instala Node.js 22 y el runtime CPU y añade un paquete temporal con comprobación HTTP e inferencia sobre una imagen blanca generada. Esto verifica funcionamiento, no precisión. [Resultados por commit en GitHub Actions](https://github.com/vcanio/Capstone2026/actions/workflows/comprobar.yml).

## 3. Arranque y API

Inicia cliente y equipo con los comandos del README. Desde otra terminal:

```bash
python -c "import json, urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:8098/api/health')))"
python -c "import json, urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:8095/api/health')))"
```

Ambas respuestas deben indicar `status: ok`; el cliente debe mostrar la revisión `linea_a_20261119_v2_3_productos_bajos`, `threshold_pct: 52.0` y `persistence: sqlite3`. `analysis_ready: false` puede ser normal antes de preparar la primera inferencia. La consola informa la dirección efectiva si el puerto solicitado estaba ocupado.

## 4. Recorrido manual con fotos propias

Usa un clon de prueba y fotos autorizadas de desarrollo, distintas del test reservado. Los nombres de estado son salidas del sistema; contrastarlos con la foto es parte de la comprobación.

| Paso | Acción | Qué comprobar |
|---|---|---|
| Foto válida | Cargar JPG/PNG/WebP frontal, nítido, menor de 10 MB y 24 MP. | Termina el análisis y muestra foto, contornos por nivel y estados. No exigir un número fijo de niveles a cualquier foto. |
| Frente abastecido y hueco visible | Analizar dos tomas con esas condiciones conocidas. | Inspeccionar si los contornos cubren las repisas y si `Suficiente` / `Reponer` es coherente. Una discrepancia se registra como error, sin modificar la expectativa para ocultarla. |
| Captura degradada | Probar una toma muy oscura o desenfocada. | Si activa el filtro, aparece `no_evaluable` y solicita otra captura. Los límites del filtro no garantizan rechazar toda imagen deficiente. |
| Persona obstruyendo | Usar una foto autorizada con persona delante de una repisa. | Si se detecta y supera el umbral de obstrucción, se rechaza como `no_evaluable` y aparece la silueta ámbar. No interpretar la obstrucción como hueco. |
| Sin niveles | Cargar una imagen ajena a una góndola. | Ausencia de detecciones exige revisión; no prueba que la góndola esté vacía. |
| Persistencia cliente | Recargar la página y reiniciar el proceso conservando `.runtime`. | Historial recuperable en ese clon; navegar con flechas no vuelve a inferir. |
| Reportes | Descargar CSV, Excel y PDF después de analizar. | Los archivos abren y corresponden a los resultados registrados; CSV depende del filtro elegido y XLSX/PDF del historial del servidor. |
| Revisión equipo | Abrir `8095`, cargar una foto y exportar un lote ZIP. | Se conservan foto, resultados y marcas del flujo de revisión; basal queda identificado como experimental. |

La cámara móvil necesita dispositivo disponible, permiso y contexto seguro del navegador. La escucha local por defecto no habilita acceso desde otro teléfono. No usar «Limpiar pasillo» sobre una sesión habitual para probar borrado: esa acción elimina el recorrido guardado.

## 5. Empaquetado y límites de plataforma

Desde un clon limpio y con los cambios confirmados en Git, construir un ZIP nuevo y probarlo siguiendo [Distribución](../Distribucion/README.md). `comprobar_paquete.py` usa una extracción temporal e imagen generada; nunca pasarle el test reservado como foto de prueba.

La definición Compose (`compose.apps.yaml`) define el volumen escribible `cliente_runtime` montado en `/app/Aplicacion_Cliente/.runtime` para conservar la base SQLite aunque la carpeta cliente esté montada en solo lectura. No obstante, esta definición no equivale a un build Docker probado ni a una prueba física en Mac, que siguen pendientes de certificación. El acceso multiusuario desde terreno requiere validar además red, cámara y persistencia; no se deduce del arranque local.

## Cómo registrar una comprobación

Guardar commit (`git rev-parse HEAD`), fecha, sistema, versión de Python, comando, salida/código de retorno y origen autorizado de la foto. Distinguir `correcto`, `fallido` y `no ejecutado`. No publicar fotos internas ni bases de sesiones como evidencia sin autorización. Una prueba funcional aprobada no es mAP, recall ni una evaluación independiente de ocupación.

[Volver al README](../README.md) · [Modelo y límites](Modelo_V3_actual.md) · [Evidencias históricas](Evidencias/README.md)
