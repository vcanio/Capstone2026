# Walmart Visión · aplicación cliente

Visor de prueba de alertas de baja disponibilidad: análisis de fotos,
resultados por nivel, revisión humana y exportación CSV para Excel.
Comparte el modelo V3 oficial y el motor de [Aplicacion](../Aplicacion/README.md).

Diseño actualizado el 11/11 siguiendo la referencia de Vicente: recorrido de
góndolas a la izquierda, fotografía central y resultados por nivel a la derecha. En móvil
el recorrido pasa a una lista horizontal y los resultados quedan debajo de la foto. El logo
vectorial se comparte con el icono de la pestaña. Los contornos se dibujan desde
`display_polygon` del modelo, conservando la geometría y los puntajes reales.
«Foto original» oculta los contornos y «Comparar» mantiene ambas vistas.

Los filtros «Con alertas», «Requieren revisión» y «Sin alertas» describen el análisis
original. Si una foto contiene alertas y lecturas ambiguas, figura en «Con alertas»;
el detalle por nivel conserva ambas situaciones. «Sin alertas» no garantiza stock físico.
Las fotos sin niveles detectados o con lecturas no evaluables requieren revisión.

«Revisado» registra que se revisó la foto y «No evaluable» indica falta de evidencia
visual según la persona. «Sin revisar» retira la revisión humana de ese nivel.
«Detalle» permite confirmar una alerta o indicar que no se observa baja disponibilidad.
Estas marcas no cambian las alertas, el índice, los contornos, el orden ni los filtros.
La interfaz conserva su CSS, colores, tipografía, logo y distribución del 11/11.
El CSV separa el resultado del análisis de la revisión humana y su fecha.
Las marcas antiguas se conservan en el guardado local; los registros de reposición
anteriores no se usan para clasificar alertas. La app no gestiona tareas de reposición.
Las flechas **← / →** recorren las fotos según el filtro y el orden actuales,
igual que Anterior y Siguiente, sin volver a analizar las imágenes. No cambian
de foto al editar texto, usar selectores o tener la cámara o el menú abiertos.
«Más opciones» reúne el CSV del filtro, ejemplo, tema y «Limpiar pasillo».
La limpieza borra las fotos, resultados y revisiones del recorrido de la memoria
y del guardado local, sin deshacer ni copia de recuperación. También descarta
las antiguas reservas de deshacer al recuperar sesiones de versiones anteriores.
No borra los archivos originales del computador ni la preferencia de tema.
La distribución y los cambios visuales están documentados en [Diseño del cliente](../Documentacion/Desarrollo/Cliente_diseno_20261111.md).

Modelo oficial adoptado el 10/11: **cierre con contornos revisados**, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`. Cliente y revisión toman el mismo predeterminado de `Aplicacion/modelos.json`; no hay otra copia de pesos del cliente. La entrega del 11/11 incluye este peso; los ZIP anteriores conservan sus pesos originales. [Ficha vigente](../Documentacion/Modelo_V3_actual.md).

Línea A usa un **índice visual preliminar de 0 a 100, con umbral 52**. No es porcentaje
físico de stock ni detector de personas u obstáculos. Revisa los contornos y la foto.
Esta entrega no constituye una evaluación final del flujo operativo.

| Aplicación | Uso | Dirección local |
|---|---|---|
| Cliente | Alertas visuales, revisión humana y CSV | http://127.0.0.1:8098 |
| Equipo | Controles técnicos, comparación, marcado y lotes de revisión | http://127.0.0.1:8095 |

## Descargar e iniciar

La [versión de prueba del 11/11](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-11)
incluye ambas apps y el modelo. Extrae todo el ZIP.

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

Cada persona ejecuta una copia local. No hay sincronización entre computadores.
El primer análisis avisa de la preparación del modelo y puede tardar más; los siguientes
muestran «Analizando foto…». El estado se consulta al servidor y se conserva al recargar
la pestaña. Al cerrar y volver a iniciar el servidor, la preparación se repite.
El recorrido usa miniaturas de hasta 160 píxeles y guardado por foto para reducir el
consumo de memoria con lotes grandes. Las imágenes originales se conservan completas.
El guardado anterior se migra automáticamente en una transacción: si falla, los datos
anteriores permanecen disponibles. Cierra otras pestañas de la app si la migración lo pide;
no borres los datos del sitio para solucionar un cierre por falta de memoria.
Carga fotos propias: el dataset y las fotos del catálogo de demostración local no se
distribuyen en este ZIP. La app del equipo exporta lotes de revisión para compartir;
la app cliente descarga la hoja CSV.

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

Prueba aislada del visor de alertas: `node Aplicacion_Cliente/Pruebas/test_alertas_cliente.cjs`.
Usa las mismas variables de Playwright/Chromium; comprueba filtros, revisión independiente,
recarga, compatibilidad con marcas anteriores, CSV y vistas de escritorio/tablet/móvil
con imágenes generadas y respuestas simuladas, sin inferencia ni datos reales.
Las capturas y el resultado quedan en `.tmp/cliente_alertas_20261111/`.
Comprueba además navegación con teclado, limpieza definitiva, reintento de borrado
fallido y cancelación de análisis al limpiar.

## Licencia

Código original del equipo: [AGPL-3.0-only](../LICENSE). Consulta [licencias y procedencia de datos/pesos](../LICENCIAS.md) y [avisos de terceros](../NOTICE.md). Los datos no reciben una licencia pública por este acuerdo sobre el código.
