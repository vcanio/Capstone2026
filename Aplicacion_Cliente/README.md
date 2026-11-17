# Walmart Visión · aplicación cliente

Visor de prueba de alertas de baja disponibilidad: análisis de fotos,
resultados estrictamente del modelo por nivel, persistencia compartida en servidor (`SQLite`)
y exportación a **CSV, Excel (`.xlsx`) y PDF**.
Comparte el modelo V3 oficial y el motor de [Aplicacion](../Aplicacion/README.md).

Diseño actualizado el 11–12/11 siguiendo la referencia de Vicente: recorrido de
góndolas a la izquierda, fotografía central y resultados por nivel a la derecha. En móvil
usa navegación de tres pasos («Góndolas», «Foto», «Plan») y selector de lente trasera
cuando el dispositivo expone varias cámaras. El logo
vectorial se comparte con el icono de la pestaña. Los contornos se dibujan desde
`display_polygon` del modelo, conservando la geometría y los puntajes reales.
«Foto original» oculta los contornos y «Comparar» mantiene ambas vistas.

Los filtros «Con alertas», «Requieren revisión» y «Sin alertas» describen el análisis
original. Si una foto contiene alertas y lecturas ambiguas, figura en «Con alertas»;
el detalle por nivel conserva ambas situaciones. «Sin alertas» no garantiza stock físico.
Las fotos sin niveles detectados o con lecturas no evaluables requieren revisión.

La interfaz muestra directamente las predicciones del modelo por nivel sin controles
de revisión humana manual (la interfaz conserva su CSS, colores, tipografía, logo y
distribución del 11/11). Si una persona obstruye frontalmente la góndola (`≥ 15 %` de un
nivel o `≥ 10 %` del encuadre sin niveles detectados), la foto completa pasa a
`no_evaluable` y muestra una silueta ámbar sutil («Persona») en el visor para señalar
el motivo de rechazo. El CSV/XLSX/PDF exporta únicamente los resultados del modelo. Los registros antiguos en el guardado local se conservan sin
alterar la clasificación de alertas; la app no gestiona tareas de reposición.
Las flechas **← / →** recorren las fotos según el filtro y el orden actuales,
igual que Anterior y Siguiente, sin volver a analizar las imágenes. No cambian
de foto al editar texto, usar selectores o tener la cámara o el menú abiertos.
«Más opciones» reúne el CSV del filtro, ejemplo, tema y «Limpiar pasillo».
La limpieza borra las fotos, resultados y revisiones del recorrido de la memoria
y del guardado local, sin deshacer ni copia de recuperación. También descarta
las antiguas reservas de deshacer al recuperar sesiones de versiones anteriores.
No borra los archivos originales del computador ni la preferencia de tema.
La distribución y los cambios visuales están documentados en [Diseño del cliente](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Cliente_diseno_20261111.md).

Modelo oficial adoptado el 10/11: **cierre con contornos revisados**, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`. Cliente y revisión toman el mismo predeterminado de `Aplicacion/modelos.json`; no hay otra copia de pesos del cliente. La entrega del 11/11 incluye este peso; los ZIP anteriores conservan sus pesos originales. [Ficha vigente](../Documentacion/Modelo_V3_actual.md).

Línea A (`v2.2`: `linea_a_20261116_v2_2_cajas_sacos_picada`) usa un **índice visual de 0 a 100 con umbral 52**, evaluado inicialmente en test ciego sobre `Ohiggins 3` (**Accuracy 97,74 %**, **F1 88,24 %** por nivel; [evaluación base del 14/11](../Documentacion/Evidencias/evaluacion_test_ohiggins3_20261114.md)) y mejorado en `v2.2` con filtro de bandejas expuestas, protección de sacos blancos y cajas máster bicolor, banda picada para producto retraído, alerta de quiebre parcial, guarda por envases oscuros y severidad operativa (**Accuracy 98,87 %**, **Recall 97,22 %**, **F1 94,59 %** en los 354 niveles de `Ohiggins 3` y revisión operativa sobre **193 fotos / 893 niveles** en 3 sets reales). Tanto las tarjetas como el CSV muestran la **severidad operativa** (`Crítica`, `Alta`, `Normal`, `Verificar`), conservan el **índice bruto** (`raw_pct`) cuando un nivel pasa a revisión y reanalizan automáticamente si cambia la revisión del motor en el servidor. No mide porcentaje físico de stock; segmenta personas (`person`, COCO clase `0`) con `yolo26n-seg.pt` mediante [`oclusiones.py`](../Aplicacion/oclusiones.py): si una persona obstruye `≥ 15 %` de algún nivel (o `≥ 10 %` sin niveles) marca la foto como `no_evaluable`, y si apenas roza bordes (`5–15 %`) descuenta esas columnas; también verifica geometría de nivel superior abierto ([`geometria_niveles.py`](../Aplicacion/geometria_niveles.py)). Carros u obstáculos sin máscara de persona siguen sujetos a verificación visual; consulta los [casos límite documentados](../Documentacion/Modelo_V3_actual.md).

La cifra de v2.2 corresponde a una reevaluación posterior sobre imágenes ya observadas, no a un test ciego nuevo. Las 193 fotos / 893 detecciones son evidencia operativa, sin acreditar precisión sobre todos los niveles de las tres capturas. [Procedimiento de comprobación y límites de Docker](../Documentacion/Verificacion_funcional.md).

| Aplicación | Uso | Dirección local |
|---|---|---|
| Cliente | Alertas visuales del modelo, `SQLite` y CSV/XLSX/PDF | http://127.0.0.1:8098 |
| Equipo | Controles técnicos, comparación, marcado y lotes de revisión | http://127.0.0.1:8095 |

## Descargar e iniciar

La [entrega final MVP](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-mvp-2026-11-16)
incluye ambas apps, el peso oficial, `yolo26n-seg.pt` para personas y los scripts reproducibles. Extrae todo el ZIP.

En Windows x64, abre `iniciar_cliente.cmd` en la raíz del paquete o
[iniciar_cliente.cmd](iniciar_cliente.cmd) desde esta carpeta. El primer inicio prepara
Python 3.12 y dependencias dentro de Aplicacion; necesita Internet. No requiere instalar
el laboratorio. Si existe el entorno de desarrollo `.venv-modelo`, lo reutiliza.

Desde un clon, el mismo iniciador funciona con el peso incluido en `Aplicacion/modelos`.
El preparador Windows también está incluido en Git.

Para macOS/Linux con Docker Desktop, desde la raíz del proyecto o paquete:

```bash
docker compose -f compose.apps.yaml up --build -d --wait
```

Abre las direcciones de la tabla. Para detener ambas apps:
`docker compose -f compose.apps.yaml down`.

Cada dispositivo guarda su vista en el navegador (`IndexedDB`) y la sincroniza automáticamente con la base compartida `SQLite` del servidor (`/api/history`), permitiendo que el supervisor consulte en otro equipo los análisis subidos en terreno. Además de la hoja CSV, «Más opciones» permite descargar **Excel (`.xlsx`)** (`/api/export/xlsx`) y un **Reporte ejecutivo (PDF)** (`/api/export/pdf`), e integra la detección automática de zonas obstruidas (`oclusiones.py`) y la verificación geométrica de nivel superior abierto (`geometria_niveles.py`).
El primer análisis avisa de la preparación del modelo y puede tardar más; los siguientes muestran «Analizando foto…». El estado se consulta al servidor y se conserva al recargar la pestaña. Al cerrar y volver a iniciar el servidor, la preparación se repite.
El recorrido usa miniaturas de hasta 160 píxeles y guardado por foto para reducir el consumo de memoria con lotes grandes. Las imágenes originales se conservan completas.
El guardado anterior se migra automáticamente en una transacción: si falla, los datos anteriores permanecen disponibles. Cierra otras pestañas de la app si la migración lo pide; no borres los datos del sitio para solucionar un cierre por falta de memoria.
Carga fotos propias: el dataset y las fotos del catálogo de demostración local no se distribuyen en este ZIP. La app del equipo exporta lotes de revisión para compartir; la app cliente descarga CSV, Excel (`.xlsx`) y reportes PDF.

## Comprobar o desarrollar

```powershell
.\iniciar_cliente.cmd --verificar
```

Desde la raíz con el entorno de desarrollo preparado:

```powershell
.\.venv-modelo\Scripts\python.exe .\Aplicacion_Cliente\app_cliente.py --check
.\.venv-modelo\Scripts\python.exe -m unittest discover -s Aplicacion_Cliente\Pruebas -v
```

La [guía del equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md) explica el marcado y
la devolución de lotes. La release del 5/11 conserva su versión anterior.

Prueba opcional de memoria y persistencia, con Node.js, Playwright y Edge instalados:
`node Aplicacion_Cliente/Pruebas/test_sesion_cliente.cjs` desde la raíz. Genera imágenes
de ruido y usa un perfil aislado, sin inferencia ni acceso al recorrido del usuario.
`WALMART_PLAYWRIGHT` permite indicar el módulo Playwright y `WALMART_CHROMIUM`, otro
ejecutable Chromium. Los resultados y capturas quedan en `.tmp/cliente_memoria_20261111/`.

## Licencia

Código original del equipo: [AGPL-3.0-only](../LICENSE). Consulta [licencias y procedencia de datos/pesos](../LICENCIAS.md) y [avisos de terceros](../NOTICE.md). Los datos no reciben una licencia pública por este acuerdo sobre el código.
