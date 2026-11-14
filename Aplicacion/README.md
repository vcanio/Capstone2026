**Entrega vigente de ambas apps (13/11):** [descarga cliente y equipo](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-13). En el ZIP, abre `iniciar_equipo.cmd`; en un clon, `Aplicacion/iniciar.cmd`. [Aplicación cliente](../Aplicacion_Cliente/README.md) (8098).

**Comparación experimental en revisión:** [comparar Línea A y franja basal](Documentacion/COMPARACION_BASAL_20261112.md) desde los ajustes del visor (incluye modo «Ambos» y etiquetado por nivel). Línea A sigue predeterminada; basal es experimental y aún no está calibrada.

# Walmart Vision · Aplicación V3

Mesa de revisión del equipo (9/11, ampliada el 12/11): marcado por nivel o zona, atajos, revisión durante el análisis, comparación de ejecuciones y algoritmos (`Línea A`, `Basal · experimental`, `Ambos`), etiquetado por nivel y lotes ZIP recuperables. Ver [guía de revisión](Documentacion/REVISION_EQUIPO.md) y [comparación basal](Documentacion/COMPARACION_BASAL_20261112.md).

El modelo oficial local es el **best.pt del cierre con contornos revisados terminado el 10 de noviembre**, adoptado por Vicente y predeterminado en ambas apps. Su SHA-256 es `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`; la copia compartida está en `modelos/V3-cierre-revisado-20261110.pt`. La entrega vigente del 13/11 y la prueba del 11/11 incluyen este peso; los ZIP anteriores conservan sus pesos originales. La ocupación sigue siendo experimental y Línea A permanece predeterminada.

- **Usar en Windows:** abrir [iniciar.cmd](iniciar.cmd). El primer inicio prepara las dependencias.
- **Usar con Docker:** ejecutar `docker compose up --build -d --wait` desde esta carpeta y abrir http://127.0.0.1:8095.
- [Manual de usuario](../Documentacion/Usar_Walmart_Vision.md) · [Guía V3](Documentacion/LEEME_V3.md) · [Modelo y límites](../Documentacion/Modelo_V3_actual.md).
- [ZIP V3 publicado y SHA-256](../Entregables/README.md).
- [Cómo leer el código de niveles y ocupación](Documentacion/LEER_CODIGO.md).
- [Documentación técnica y registros](Documentacion/) · [Pruebas de la aplicación](Pruebas/).

La app usa **Línea A** para el índice de disponibilidad visual por nivel: normalización compartida por góndola, evidencia híbrida y penalización por hueco continuo. **Reponer** con índice menor a **52 / 100**, **Suficiente** desde 52 cuando no hay ambigüedad y **Revisar** por señal ambigua o recorte. Evaluado en frío sobre el test de **Ohiggins 3** (68 fotos, 354 niveles ciegos: **Accuracy 97,74 %**, **Precision 93,75 %**, **Recall 83,33 %**, **F1 88,24 %** por nivel y **89,80 %** por foto), sigue siendo un índice visual y no un porcentaje físico de stock. Los resultados previos guardados se descartan al recuperar la sesión si pertenecen al estimador anterior; las fotos y las marcas se conservan. Véase `Documentacion/LINEA_A_20261108.md`.

La confianza inicial de YOLO es 0,60 y puede ajustarse desde 0,25. La app no detecta automáticamente personas ni obstáculos: revisa la visibilidad y los contornos. La sesión se guarda en el navegador y no se incorpora al entrenamiento.

La exclusión de barandas fragmentadas sigue pendiente de revisión visual. La [descarga histórica del 5 de noviembre](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.zip) conserva el peso y el estimador de su propia publicación. La entrega conjunta del 11/11 incorpora el oficial del 10/11 y Línea A.

Los archivos del programa y el modelo se conservaron durante el traslado. Los documentos de verificación con fecha anterior describen su propia entrega.

## Desarrollar desde un clon

El repositorio incluye el manifiesto, el peso oficial y el preparador de Windows. Clona el proyecto y abre `Aplicacion/iniciar.cmd` en Windows, o ejecuta `docker compose up --build -d --wait` desde `Aplicacion` para usar Docker. La primera preparación requiere Internet. El código de main puede ser más reciente que el ZIP de la release.

La corrección de barandas sigue pendiente de revisión visual y el mapa de señal se muestra en fucsia. Tras modificar los módulos incluidos en `edge_sources`, actualiza sus SHA-256 en `modelos.json` para que la aplicación pueda verificar su integridad.

Para comprobar el código y construir paquetes desde un clon, consulta [Distribución y pruebas](../Distribucion/README.md). No se necesita el laboratorio interno.

Tras actualizar, vuelve a analizar las fotos guardadas en el navegador para obtener resultados del modelo oficial.

## Licencia

Código original del equipo: [AGPL-3.0-only](../LICENSE). Consulta [licencias y procedencia de datos/pesos](../LICENCIAS.md) y [avisos de terceros](../NOTICE.md). Los datos no reciben una licencia pública por este acuerdo sobre el código.
