# Revisión de fotos · equipo de desarrollo

Versión: `revision_equipo_20261109_v1` · 9 de noviembre de 2026.

Esta entrega es la mesa de pruebas de desarrollo. La aplicación cliente está separada. Usa el modelo V3 oficial y Línea A `linea_a_20261108_contornos_conservados`, índice visual 0–100 con umbral 52. Su ajuste sigue siendo preliminar; el índice no es porcentaje físico de stock. No detecta automáticamente personas ni obstáculos.

## Empezar en otro equipo

1. Extrae **todo** el ZIP a una carpeta con permiso de escritura. No ejecutes desde dentro del ZIP.
2. En Windows, abre `iniciar.cmd`. El primer inicio necesita Internet para preparar Python y las dependencias. Después abre `http://127.0.0.1:8095`.
3. En macOS/Linux, usa las instrucciones de `DOCKER.md` incluidas en el paquete.
4. Escribe tu nombre en **Revisor** y selecciona hasta 50 fotos JPG, PNG o WebP, de hasta 10 MB cada una y 500 MB por lote.
5. Pulsa **Analizar fotos**. La confianza inicial es 0,60. Puedes revisar las fotos terminadas mientras se analizan las siguientes; la cola no cambia la foto seleccionada.

Cada integrante ejecuta su copia local. Esta versión no comparte una base de datos ni sincroniza sesiones entre equipos. Las fotos se procesan localmente y no entran al entrenamiento.

## Revisar rápido

| Acción | Tecla / control |
|---|---|
| Marcar correcta | **A** |
| Registrar un fallo | **F** (también M por compatibilidad) |
| Elegir motivo en el editor | **1–7** |
| Guardar y continuar | **Enter** |
| Foto anterior / siguiente | **← / →** |
| Comparar original y resultado | **C** |
| Deshacer la última marca | **Z** |

Los atajos generales no actúan mientras escribes en un campo. Enter dentro de la nota permite escribir otra línea. **Avanzar al guardar** busca la siguiente foto analizada y sin revisar dentro del filtro seleccionado; puede desactivarse. Si no quedan fotos listas, espera la cola o cambia de filtro. Deshacer conserva la foto y el resultado; no se aplica a una ejecución que ya cambió.

**Correcta** significa que revisaste la detección, los contornos y la recomendación visibles en esa ejecución. No es una certificación automática del modelo. Una foto con niveles omitidos también puede mostrar todos sus niveles detectados suficientes: comprueba siempre el original.

## Señalar fallos

- Usa **Señalar fallo en nivel N**, o abre **Registrar fallo** y haz clic en un contorno dentro del editor.
- Para un nivel omitido, elige **Señalar zona / nivel omitido** y arrastra un rectángulo sobre la foto. Puedes marcar la foto completa si no corresponde a un único nivel.
- Elige el motivo. Los motivos distinguen detección, geometría y decisión de disponibilidad. Se propone un resultado esperado que puedes cambiar.
- Añade una nota cuando ayude a entender el caso.
- **Guardar y añadir otro** conserva la misma foto y permite registrar otro problema. Cada incidencia conserva su nivel o zona, revisor, fecha, resultado obtenido y ejecución de origen.

La zona marcada es evidencia humana de revisión, no una modificación del polígono YOLO ni una anotación enviada a CVAT. Retirar una incidencia permite corregir una marca equivocada; puede deshacerse.

## Comprobar un ajuste

1. Guarda el lote mediante **Descargar lote** antes de cambiar de equipo o de versión.
2. En la aplicación nueva, usa **Abrir lote de revisión** y selecciona ese ZIP sin recomprimirlo. Recupera las fotos y las incidencias. Si modelo o estimador cambiaron, el resultado anterior queda como referencia y se solicita un análisis nuevo.
3. Usa **Reanalizar esta foto** o **Reanalizar lote** con la configuración elegida. El lote conserva la última ejecución anterior para comparar y mantiene las incidencias históricas. Una ejecución nueva requiere una revisión nueva.
4. Abre **Incidencias e historial** y compara las imágenes anterior y actual. Registra **Corregido**, **Persiste** o **Empeoró / nuevo fallo**. Esa comparación es humana y no marca por sí sola toda la foto como correcta.
5. Confirma la foto actual con A o registra sus fallos con F. Descarga el lote actualizado.

Pausar o cancelar termina la foto que está en curso y conserva lo completado. **Analizar pendientes** permite continuar también un reanálisis pausado. Si un reanálisis falla, el resultado anterior se conserva y se avisa del error; **Reintentar fallidas** vuelve a intentarlo.

Usar fotos de desarrollo y fotos nuevas autorizadas. Mantener test reservado: no cargarlo para ajustes, selección ni demostración. No cambiar las particiones existentes. Las fotos sintéticas deben identificarse y analizarse aparte al evaluar resultados.

## Qué recibe quien corrige los problemas

**Descargar lote** incluye todo el lote, respetando los originales:

- `originales/`: bytes originales de las fotos.
- `contornos/`: referencia de los contornos de la ejecución actual.
- `marcas/`: zonas humanas F1, F2… en el orden de las incidencias de `revision.json`; pueden pertenecer a ejecuciones anteriores.
- `resultados/` y `anteriores/`: resultados y última referencia anterior para reproducir la comparación.
- `revision.json`: estados, incidencias, configuración, modelo, hashes, revisión del estimador, autores y fechas UTC.
- `resumen.csv`: tabla para Excel; contiene también las incidencias históricas.
- `resumen.json`: recuento por motivo y comparación. No representa tasas de precisión.

El estado **sin_revisar** se mantiene cuando faltan resultados o la revisión pertenece a una ejecución anterior. La app avisa si hay fotos pendientes antes de descargar. No confundir la presencia de incidencias históricas con fallos confirmados en el resultado actual: consulta `analysis_id`, el estado de revisión y la comparación.

La sesión se guarda en este navegador y origen local (misma dirección y puerto); depende del espacio disponible. El ZIP es el respaldo portable para compartir con el equipo. Si el navegador avisa que no pudo guardar, descarga el lote antes de cerrar. No se envía automáticamente a nadie.

Los análisis nuevos también quedan como cambios pendientes hasta preparar el ZIP. La descarga representa una instantánea del lote: los cambios posteriores siguen pendientes. En incidencias antiguas sin dimensiones de referencia recuperables, el ZIP conserva los datos y `resumen.json` advierte que no se pudo dibujar esa marca con certeza.

Esta entrega no inicia entrenamientos ni actualiza la release publicada del 5 de noviembre. Solo Vicente inicia entrenamiento desde el panel.
