# Laboratorio de modelos · V3 estable

El laboratorio abre siempre V3 y toma el modelo de `.config-modelo/version_actual_v3.json`. El punto de partida es el **best.pt aceptado por Vicente**; [Modelos/Actual](../../Modelos/Actual/README.md) documenta su ubicación. Las preferencias antiguas del navegador ya no cambian la versión activa.

Para analizar fotografías, abrir [Walmart Vision](../../Aplicacion/README.md). El laboratorio se centra en preparar datos, entrenar y revisar métricas y decisiones. El enlace **Abrir app de revisión** está disponible en todas las secciones y abre la app del equipo en el puerto 8095. La sección de probar fotos se retiró del flujo operativo.

## Abrir

Desde la raíz del proyecto:

```powershell
& ./Laboratorio/Modelos/abrir_panel.ps1
```

Panel: http://localhost:8090. `iniciar_panel.ps1` admite `-Cpu`, `-Build`, `-Dev` y `-ConCvat`. En desarrollo, los cambios de interfaz se recogen al recargar y los de Python requieren reiniciar el servicio cuando no haya trabajos activos. Una instalación sin montaje de código necesita reconstruir la imagen con `-Build`. [Instalación y Docker](../../Infraestructura/Docker/README.md).

El inicio permite elegir **Segmentación de niveles** o **Clasificación de visibilidad**. Cada espacio muestra sus propias secciones; «Cambiar modelo» vuelve al menú sin modificar los datos ni iniciar trabajos.

## Trabajo habitual

1. **Preparar datos:** consultar las tareas de la partición activa, revisar las regiones visibles y exportar con identificación del revisor. El cierre revisado completado contiene 267 imágenes: 256 train (203 reales/53 sintéticas) y 11 val reales, con 1.298 y 55 polígonos respectivamente. Un futuro refuerzo requiere un plan nuevo. Consultar CVAT no modifica polígonos ni aprueba pendientes.
2. **Entrenar segmentación:** elegir datos revisados y configurar el próximo refuerzo desde el best.pt oficial: máximo 40 épocas, paciencia 10 y lr 0,0001. Solo Vicente inicia el ensayo al pulsar **Iniciar entrenamiento de segmentación**.
3. **Resultados y decisión:** consultar métricas y curvas, con validación real y diagnóstico sintético separados. La aceptación del modelo oficial se muestra como registro; las decisiones editables corresponden a otros ensayos. Registrar un candidato no reemplaza el modelo oficial.
4. **Clasificación de visibilidad:** revisar las etiquetas de sus fotos, entrenar y consultar resultados desde su espacio independiente. Revisar estas anotaciones sigue siendo parte de la preparación del clasificador.

El inicio resume el estado y da acceso a los tres pasos sin iniciar trabajos. La app de revisión conserva su configuración y no selecciona automáticamente el candidato del laboratorio.

El catálogo operativo omite inventarios V1/V2, exportaciones de particiones sustituidas, planes cerrados y el piloto antiguo de módulos. Los ensayos nuevos con pesos siguen disponibles para evaluación. Las actualizaciones del catálogo conservan el borrador del usuario; cambiar exportación o selección aplica los valores correspondientes.

## Datos y límites

Las subidas históricas permanecen en `Laboratorio/Experimentos/panel_pruebas/Subidas_panel/`, aisladas de los datos y del entrenamiento. La interfaz operativa ya no carga los módulos de predicción V3 ni la galería de reserva final. Los controles V1/V2 quedan inertes, fuera de la navegación, por compatibilidad con el controlador histórico; sus APIs y registros se conservan. Las escenas y sus variantes conservan grupo y partición. Los repartos anteriores conservan su alcance histórico. El test histórico actual de 63 fotos permanece reservado; las 68 fotos de Ohiggins 3 tienen revisión visual humana y siguen fuera de train.

V3 aprende una clase `Nivel`. En Walmart Vision, ocupación y alertas siguen siendo experimentales y la visibilidad la confirma el usuario. Se mantienen los incidentes de `le_g10`: el superior de la 029 queda demasiado alto y el de la 030 puede omitirse. La adopción del afinado no demuestra una mejora global; las métricas de cada etapa conservan su partición y condiciones de comparación.

## Código y comprobaciones

| Archivo | Función |
|---|---|
| `panel.html`, `static/` | Interfaz y módulos del laboratorio. |
| `panel_modelos.py`, `panel_worker.py` | API local y ejecución de trabajos. |
| `preparacion_v3.py`, `selecciones_v3.py` | Revisión, exportaciones y selecciones. |
| `entrenamiento_v3.py`, `prediccion_v3.py` | Entrenamiento y evaluación geométrica. |
| `tests/` | Regresiones de integridad, API y formularios. |

`/api/catalog/current` sirve el catálogo operativo con caché, compresión y ETag. `/api/catalog` y los módulos V1/V2 conservan compatibilidad técnica con registros y pruebas históricos, fuera de la navegación habitual. Se conservan datasets, fuentes y metadatos congelados.

[Guía de entrenamiento V3](../../Documentacion/Desarrollo/Entrenamiento_geometrico_V3.md) · [Probar modelos V3](../../Documentacion/Desarrollo/Probar_modelos_V3.md) · [Historial de modelos y decisiones](../../Documentacion/Desarrollo/Historial_modelos_y_cambios.md) · [Experimentos vigentes](../Experimentos/README.md) · [Antecedentes](../../Historico/README.md).
