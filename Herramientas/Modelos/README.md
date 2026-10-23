> Este panel es una herramienta del **equipo de desarrollo** para preparar datos, entrenar y evaluar. Para usar la aplicación con fotografías propias, seguir [Usar Walmart Visión](../../Documentacion/Usar_Walmart_Vision.md). Para instalar el laboratorio en otro computador, consultar la [guía técnica](../../Documentacion/Desarrollo/Replicar_proyecto.md). El inicio Docker base no necesita CVAT; para traer anotaciones usar -ConCvat y configurar acceso personal.

# Panel de niveles y disponibilidad

**Estado al 23/10/2026:** este panel mantiene los ensayos V1/V2. El trabajo de anotación actual es V3, con 458 imágenes y partición 327/68/63, pero su exportación y entrenamiento siguen bloqueados hasta implementar y revisar ese flujo. [Estado de datos](../../Datos/Registros/README.md). Las instrucciones de tres estados de abajo corresponden a V2, no al objetivo geométrico único de V3.

Esta carpeta contiene el código del laboratorio. Los modelos generales están en [Modelos](../../Modelos/README.md) desde la raíz, y los resultados de entrenamiento en [Experimentos](../../Experimentos/README.md).

| Archivo o carpeta | Función |
|---|---|
| `panel.html` | Estructura y contenido del panel. |
| `static/` | Estilos CSS y scripts JavaScript del panel, separados por función. |
| `panel_modelos.py`, `panel_worker.py` | Servidor local y ejecución de los trabajos. |
| `entrenar_niveles.py` | Entrenamiento por consola con el criterio V2 de tres estados. |
| `tests/` | Pruebas de datos, servidor y comportamiento del panel. |

El código de Walmart Visión, la aplicación para usuarios, está en [Herramientas/Demo_lite](../Demo_lite/LEEME.md).

La interfaz se adapta al **criterio del dataset y del modelo seleccionado**.
Los selectores identifican v1 (4 estados), v2 base (2 estados) y v2 completo
(3 estados, cuando exista un ensayo con esas clases). La ayuda, los colores y
las métricas corresponden a ese perfil. Los modelos v1 se conservan para mostrar
la primera versión. [Evolución, scripts y guía de demostración](../../Documentacion/Desarrollo/Evolucion_v1_v2.md).

Para entrenar por consola con el **criterio nuevo de tres estados** (`reponer`,
`suficiente`, `no_evaluable`), usar `entrenar_niveles.py`. Está comentado e incluye
`--solo-verificar` y `--verificar-entorno`, copia de datos por ensayo y métricas de
reposición por clase. Las dependencias locales de `requirements.txt` comparten
las versiones de Docker. Véase la [guía de entrenamiento v2](../../Documentacion/Desarrollo/Entrenamiento_niveles_v2.md).
Requiere un dataset YOLO de segmentación preparado con esas clases.

El panel también admite ahora la **etapa base v2 de Líder Express**: importar la
tarea 19 completa, registrar la revisión y entrenar `Nivel_reponer` y
`Nivel_suficiente`. Usa automáticamente la partición fijada: 160 fotos para
entrenamiento y 10 reales para validación. Las 30 variantes de diagnóstico y las
36 imágenes de evaluación final se conservan fuera de la exportación. Las copias
importadas antes de esta adaptación deben volver a importarse; no se cambian sus
anotaciones ni los ensayos históricos. La etapa con obstáculos se prepara después.

Flujo: **Preparar datos → Cargar proyectos y tareas de CVAT → proyecto 7 / tarea
19 → Traer anotaciones del lote → registrar revisión → Entrenar**. El informe
muestra las dos clases y el uso de cada foto. El nombre de ensayo debe ser nuevo.
Se recomienda partir de pesos generales para comparar la nueva base. El panel
mantiene compatibles los modelos v1 de cuatro estados.

El lote histórico v1 usa la **guía v1.3**, tarea 16, proyecto 6, jobs 36/37/38.
El lote nuevo usa la [guía v2 de Líder Express](../../Documentacion/Desarrollo/Guia_anotacion.md).

## Abrir y usar

Desde la raíz del proyecto:

```powershell
& .\Herramientas\Modelos\abrir_panel.ps1
```

Panel: http://localhost:8090. Para iniciar el contenedor directamente, usar `iniciar_panel.ps1`; admite `-Cpu` y `-Build`. [Docker](../../Infraestructura/Docker/README.md).

Para desarrollo, `iniciar_panel.ps1 -Dev` monta el código local: los cambios de interfaz se ven con F5. Los cambios de Python requieren reiniciar el servicio sin entrenamientos activos; las dependencias requieren reconstrucción. Véase la [guía de desarrollo](../../Infraestructura/Docker/README.md#desarrollo-del-panel).

0. **Resumen de trabajo:** el panel recuerda la versión, copia y ensayo válidos y consulta su estado actual. El inicio separa datos, ensayo, evaluación y ocupación/alertas, y ofrece una siguiente acción con su motivo. V1, V2 y el piloto conservan su flujo; V3 muestra sus dependencias de preparación y no habilita entrenamiento por seleccionar la tarjeta. **Cambiar versión** vuelve al inicio. Una copia nueva pendiente conserva el acceso a modelos históricos utilizables.
1. **Preparar datos:** actualizar CVAT manualmente, seleccionar la tarea completa, traer sus anotaciones, revisar incidencias, balance y partición y registrar quién revisó niveles y estados. Importar no cambia dibujos de CVAT ni inicia entrenamientos.
2. **Entrenar:** elegir la copia revisada, el modelo general y los ajustes. Un solo trabajo usa la GPU a la vez. Cada ejecución crea su carpeta y conserva configuración, snapshot, partición, pesos y resultados; reutiliza el dataset de su versión si coincide por SHA-256.
3. **Comparar resultados:** revisar alertas, métricas por estado, fotos, curvas y omisiones. Las diferencias automáticas requieren fotos, etiquetas y partición coincidentes.
4. **Probar una foto:** pulsar **Subir mi foto** para elegir o arrastrar un JPG, PNG o WebP propio (hasta 15 MB y 24 megapíxeles), o elegir **Fotos del proyecto**. Seleccionar YOLO11-1 o YOLO26-1 y pulsar **Analizar foto**. La imagen muestra niveles numerados, colores y estados; **Original**, **Niveles**, **Bordes** y **Comparar** permiten revisar el análisis. **Bordes** muestra directamente el mapa de señal cuando se analiza con YOLO + detección de bordes; en esa pestaña se puede alternar entre el mapa, los bordes de los niveles y los bordes de toda la foto. **Comparar** presenta la original junto a los niveles detectados. El resumen distingue vacío, baja, suficiente y no evaluable. La confianza y otros parámetros quedan en **Ajustes de detección**.

Las fotos propias se guardan orientadas y sin metadatos EXIF en `Experimentos/panel_pruebas/Subidas_panel/`, fuera del inventario, las copias anotadas y el entrenamiento. Se limitan a 4096 píxeles por lado para acotar la memoria de las máscaras. No se incorporan automáticamente al dataset ni se asocian anotaciones por coincidencia de nombre. La inferencia se ejecuta en el equipo local. Una foto propia sin referencias permite observar predicciones, pero no calcular precisión. La confianza del modelo no es el porcentaje de ocupación del nivel.

En **Fotos del proyecto**, el selector y las miniaturas excluyen las imágenes usadas para entrenar el modelo seleccionado, incluidos sus entrenamientos locales anteriores si se continuó desde otro modelo. Cambiar el modelo actualiza las fotos disponibles. Para los modelos v2 base actuales quedan 40 fotos revisadas de desarrollo: las 10 originales y sus 30 variantes, en una sola lista y con los nombres existentes. La reserva final sigue aparte. Las variantes se comparan con las anotaciones de la copia revisada que dio origen al modelo. El servidor también rechaza solicitudes de prueba con fotos del proyecto usadas en ese entrenamiento. Las comparaciones históricas conservan todas sus fotos.

**Probar una foto** es la evaluación de desarrollo: permite revisar errores con validación y fotos nuevas para decidir ajustes de YOLO, confianza y el método de Paulo. Analizar una foto no reentrena el modelo. La reserva final queda fuera del selector y las miniaturas; se utiliza después de fijar los modelos y parámetros que se quieren evaluar. En v2 base, la evaluación final principal usa 9 originales reales y las 27 variantes sintéticas se informan como diagnóstico aparte. La subida manual admite cualquier foto válida, por lo que para estas pruebas habituales deben elegirse fotos nuevas o de desarrollo, conservando la reserva para el cierre.

La interfaz conserva selecciones y ajustes en el navegador. Las imágenes permiten zoom y arrastre. El seguimiento del trabajo local actualiza progreso y resultados; la consulta de anotaciones de CVAT sigue siendo manual.

Una copia aprobada muestra su comprobante de revisión. **Configurar entrenamiento con esta copia**, **Ver resultados de este ensayo** y **Probar este modelo** conservan los identificadores correspondientes. Entrenamiento admite un propósito opcional. Resultados permite registrar una decisión con motivo y autor, conservando historial; terminar un entrenamiento no equivale a validar el modelo. Las diferencias automáticas requieren un protocolo de evaluación registrado y compatible; los históricos sin él conservan comparación visual. [Implementación y comprobaciones del flujo](../../Documentacion/Desarrollo/Implementacion_laboratorio_modelos_20261022.md).

Las nuevas predicciones numeran los niveles de abajo hacia arriba y, en una misma fila, de izquierda a derecha, tolerando pequeñas diferencias de altura por perspectiva. La imagen y la tabla comparten el mismo orden. Los números identifican detecciones dentro de esa foto; no corresponden al `nivel_id` de CVAT ni se mantienen entre fotografías.

## Copia y ensayos actuales

La copia histórica v1 es `datos_20261015_012453_4ba1d339`, estado `lista_niveles`, con revisión de Vicente registrada el 14 de octubre de 2026, hora de Santiago. Contiene 91 fotos: 86 de entrenamiento y 5 reales de validación; respeta 11 exclusiones de la tarea 16. Convive con la copia v2 base de la tarea 19. Los siete originales de reserva final del primer lote quedan fuera del desarrollo.

Se conservan **YOLO11-1** y **YOLO26-1**, con los mismos datos y partición. [Revisión YOLO11](../../Experimentos/YOLO11-1_20261015_013749_f709/REVISION_MODELO.md) · [Comparación YOLO26/YOLO11](../../Experimentos/YOLO26-1_20261015_021212_c452/REVISION_MODELO.md).

`Experimentos/panel_pruebas/` conserva únicamente solicitudes, logs y pruebas de esos ensayos. Las copias previas y demás experimentos están en `.resguardo/limpieza_20261015/historico`, fuera del catálogo activo.

## Criterio y exportación

En v1, YOLO aprende cuatro clases de segmentación: `Nivel_vacio`, `Nivel_baja_disponibilidad`, `Nivel_suficiente` y `Nivel_no_evaluable`. En v2 base aprende `Nivel_reponer` y `Nivel_suficiente`; el criterio v2 completo añade `Nivel_no_evaluable`. El estado se convierte en clase; los IDs, integridad y observaciones son auxiliares opcionales. Los estados pendientes, geometrías inválidas y problemas de partición bloquean la aprobación.

La regla usa el ancho completo del nivel, cuenta producto visible al fondo y define baja por debajo del 30 %. Si una ocultación puede cambiar el estado, corresponde no evaluable. Vacío y baja generan alerta; no evaluable se comunica por separado. El 30 % es un criterio inicial pendiente de calibración.

El panel exporta fotos completas una vez por versión en Datos/Registros/Versiones_modelos/<version>/exportaciones/dataset_niveles. Los ensayos usan dataset_ref para compartir esa exportación verificada, sin repetir imágenes y etiquetas por modelo. La copia aprobada mantiene snapshot y partición comprobados por hash. Importar cambios de CVAT crea o reutiliza la copia correspondiente y requiere revisión antes de un nuevo entrenamiento.

Los modelos generales locales son `yolo11n-seg.pt` y `yolo26n-seg.pt`. El entorno Docker usa Ultralytics 8.4.174, PyTorch 2.5.1 y CUDA 12.1. Los módulos piloto_modulos.py y comparar_niveles.py participan en el entrenamiento y evaluación; conjuntos.py resuelve y verifica la exportación compartida.

## Evaluación y siguiente trabajo

El código local incorpora un [ajuste visual de contornos a cuatro vértices](../../Documentacion/Desarrollo/Posprocesamiento_contornos_niveles.md), con lados rectos y perspectiva. No requiere reentrenar: conserva máscaras, clases y confianza de YOLO. Las métricas y la ocupación siguen usando las máscaras originales. El registro del 22 de octubre documenta 21 pruebas técnicas y una comprobación visual en una foto conocida; no acredita una mejora de precisión. Volver a analizar la foto genera el nuevo dibujo; los resultados históricos no se sobrescriben.

La validación histórica v1 tiene 34 niveles suficientes y 2 no evaluables; no contiene vacíos ni bajos. La validación principal v2 base contiene 50 suficientes y un nivel reponer. La cobertura real de faltantes sigue siendo escasa. Consultar el [registro de división](../../Datos/Registros/Particiones/lider_express_v2_20261019/README.md).

`metricas_alertas.json` registra omisiones, falsas alertas, matriz de confusión y métricas por estado. La comparación guardada usa confianza 0,25 e IoU de máscara de al menos 0,5 para emparejar referencias. Un estado ausente tiene recall no disponible. Las máscaras binarias permiten evaluar sin depender de contornos convertidos que puedan ser inválidos.

## Comprobaciones técnicas

El sondeo lee progreso y registros de los trabajos activos en cada consulta. Los terminados se conservan en memoria y sus archivos se comprueban cada 15 segundos; las ediciones externas pueden tardar ese intervalo en aparecer. La caché conserva como máximo los 30 trabajos recientes. El catálogo reutiliza JSON, compresión y ETag: una consulta sin cambios devuelve 304 sin descargar ni procesar de nuevo el catálogo completo. Las operaciones del panel invalidan el catálogo; los cambios externos se recogen al vencer su caché (5 segundos durante un trabajo, 15 en reposo).

Los colores se definen al inicio de `static/panel.css`: `:root` contiene la paleta clara y `:root[data-theme=dark]` sus variaciones. Componentes y gráficos SVG consumen las mismas variables semánticas (`--paper`, `--ink`, `--warning-surface`, etc.). Los colores de disponibilidad se mantienen alineados con las máscaras generadas por el modelo.

Las pruebas están agrupadas en tests/. Desde la raíz del proyecto:

```powershell
& ./.venv-modelo/Scripts/python.exe -m unittest discover -s Herramientas/Modelos
```

`servidor_prueba_interfaz.py` ofrece escenarios ficticios para revisar la interfaz sin entrenar ni modificar CVAT.

## Evaluar los pesos actuales sobre las 40 fotos de desarrollo

Ejecutar `.venv-modelo/Scripts/python.exe Herramientas/Modelos/evaluar_desarrollo.py --run <nombre_del_ensayo>`. Usa los mejores pesos existentes a confianza 0,25 e IoU de máscara 0,5; no entrena ni cambia la partición, exportaciones o métricas históricas. Guarda `evaluacion_desarrollo.json` en el ensayo con los resultados por foto, por estado, alertas acertadas, omitidas y falsas. El panel muestra este resumen en Comparar resultados.
