# Informe intermedio de avance
## Walmart Computer Vision

**Corte:** 20 de octubre de 2026, hora de Santiago. **Destinatario:** José Larraín. **Docente guía:** Arturo Vargas, DUOC UC.

**Equipo:** Vicente Canio, Paulo Guerra y Vicente Vilches.

**Revisión:** 21 de octubre de 2026. Actualizamos los casos con YOLO + detección de bordes y la entrega Walmart Visión. El corte de los datos y entrenamientos sigue siendo el 20 de octubre; la planificación conserva el inicio aproximado en agosto.

El prototipo localiza y clasifica repisas en fotografías. El análisis adicional de bordes, color y textura aporta mapas para revisar producto y huecos. Los casos nuevos muestran respuestas favorables en algunos envases y fallos en productos blancos, fondos metálicos y cobertura de niveles. Esa señal todavía no mide ocupación real ni cambia los estados YOLO. Faltan etiquetas de referencia para evaluar cuantitativamente esta selección.

| Antecedente de datos y modelos YOLO | Resultado al 20 de octubre |
|---|---|
| Imágenes propias únicas | 405: 96 reales y 309 sintéticas |
| Datos usados en V1 | 86 entrenamiento y 5 validación real |
| Datos usados en V2 base | 160 entrenamiento y 10 validación real |
| Mejor mAP50–95 de máscaras V2 | 92,79 %, YOLO26n, sobre 10 fotos reales |
| Alertas reales de validación V2 | 1 acertada de 1; cero falsas en YOLO26n |
| Modelos V2 de tres estados | Pendientes de entrenamiento y evaluación |

YOLO26 V2 encontró 50 de los 51 niveles de validación y acertó esos 50 estados. Detectó la única alerta real de reposición y no generó falsas alertas. Este resultado comprueba un caso de faltante; necesitamos más ejemplos para saber cuántos detectaría en una tienda. Separamos fotos reales y modificadas con IA. La validación sirve para elegir modelos durante el desarrollo; la prueba final sigue reservada.

El alcance es disponibilidad visual por nivel en fotografías estáticas. El sistema asigna un estado aprendido; no mide inventario de bodega, profundidad, unidades por SKU ni un porcentaje continuo de ocupación. El umbral del 30 % sigue siendo un criterio inicial de anotación pendiente de calibración con el cliente.

**Contenido:** estado y planificación; documentación técnica; resultados preliminares y 20 casos visuales; reproducibilidad y GitHub; conclusiones y plan de mejora.


<!-- page -->

## Guía de lectura del informe

El informe sigue los cinco puntos del encargo: avance, solución técnica, resultados, reproducibilidad y próximos pasos. Mostramos lo que funciona y lo que falta. Los nombres de archivos permiten localizar la evidencia; no es necesario memorizarlos para comprender los resultados.

| Concepto | Qué significa en nuestro proyecto |
|---|---|
| Nivel de góndola | Espacio de una repisa que revisamos como unidad; no contamos cada producto por separado. |
| Segmentación y máscara | Dibujar el contorno del nivel. La región dibujada se llama máscara. |
| Estado o clase | Categoría asignada al nivel, como reponer o suficiente. Un contorno correcto puede tener un estado equivocado. |
| Etiqueta o referencia | Contorno y estado revisados por personas; los usamos para enseñar al modelo y comparar resultados. |
| Entrenamiento e inferencia | Entrenar es aprender con ejemplos. Inferir es usar lo aprendido para analizar otra imagen. |
| Pesos y ensayo | Los pesos guardan lo aprendido. Un ensayo conserva esos archivos, la configuración y sus resultados. |
| Dataset y partición | El dataset es el conjunto de datos. Lo dividimos en entrenamiento, validación y prueba final. |
| Oclusión | Una persona, carro o caja tapa el nivel y puede impedir decidir su disponibilidad. |
| Versión fija o snapshot | Copia guardada de datos y etiquetas para saber exactamente con qué ejemplos trabajamos. |

Las imágenes de entrenamiento permiten aprender y revisar fallos. Las de validación permiten comparar modelos y ajustes. La prueba final se consulta después de fijar esas decisiones; usarla para escoger ajustes dejaría de ser una comprobación final independiente del desarrollo.

Cada caso compara tres vistas: fotografía original, salida de YOLO y mapa de señal de bordes. Revisamos si encontró las repisas, si el estado es razonable y si la señal coincide visualmente con los productos. El criterio de calidad se indica en cada ficha; la tabla histórica de métricas YOLO se presenta por separado.

Una explicación ampliada y un glosario están en Documentacion/Guia_para_entender_el_proyecto.md. La relación con cada requisito del encargo está en Documentacion/Desarrollo/Revision_de_requisitos_informe.md.

<!-- page -->

## 1 Estado de avance del proyecto

Para estimar el avance, dividimos cada módulo en cuatro hitos de igual peso. Cada hito cumplido aporta 25 puntos. Hemos cerrado 28 de 36 hitos, equivalentes al 77,8 %. Es una estimación del trabajo implementado: no es la precisión del modelo ni significa que quede exactamente el 22,2 % del esfuerzo.

| Módulo | Hitos cerrados | Avance y estado | Evidencia |
|---|---|---|---|
| Datos | Captura, inventario, integridad | 75 % en desarrollo | Datos/Registros/lotes.json |
| Etiquetado en equipo | Configuración, tareas, usuarios y acceso | 100 % implementado | Infraestructura/CVAT y tareas 16, 19, 22 |
| Separación de datos | Familias, grupos, listas y comprobación | 100 % implementado | Particiones/lider_express_v2_20261019 |
| Importación y exportación | Leer etiquetas, revisar y guardar para YOLO | 100 % implementado | datos_modelos.py y conjuntos.py |
| Modelos base | V1 YOLO11/26, V2 base YOLO11/26 | 100 % para esta etapa | Cuatro ensayos en Experimentos |
| Panel | Carga, inferencia, comparación | 75 % en desarrollo | panel_modelos.py y panel_worker.py |
| Distribución | Arranque Windows y Docker de Walmart Visión | 75 % en desarrollo | Infraestructura/Docker y Entregables |
| Oclusiones V2 | Lote y partición preparados | 50 % en desarrollo | 60 imágenes y tarea 22 |
| Cierre de calidad | Diagnóstico de errores | 25 % en desarrollo | evaluacion_por_imagen.json |

**Hitos restantes:** datos: ampliar faltantes reales; panel: aceptación con tres estados; distribución: instalación de Walmart Visión en otro computador físico; oclusiones: revisión final de etiquetas y ensayo de tres estados; cierre: deduplicación, prueba final y aceptación del MVP.

“Implementado” indica que existen código, configuración o artefactos comprobables. La preparación posterior de la entrega verificó el arranque Docker en CPU y la demo Lite con los cuatro modelos, sin requerir CVAT. Esto no equivale a disponibilidad garantizada del CVAT compartido ni a una prueba en otro computador físico; el registro actualizado está en reproducibilidad/VERIFICACION.md.

Los cuatro entrenamientos guardan sus pesos, ajustes, resultados, grupos de datos y versiones de programas. V2 base utilizó la copia aprobada datos_20261019_234626_3df2e643. Esa copia permite comprobar con qué se entrenó, aunque algunos textos antiguos de los lotes sigan diciendo que falta exportar. La aprobación no incluye las etiquetas con obstáculos de la tarea 22.


<!-- page -->

## 1 Planificación desde el inicio del proyecto

![Carta Gantt histórica y propuesta de cierre](Evidencias/gantt_20261020.png)

El proyecto comenzó aproximadamente en agosto de 2026, según la reconstrucción del equipo. La Gantt incorpora la historia de trabajo y el cierre propuesto. La detección de bordes comenzó en la semana 9 y se integró con el modelo YOLO en la semana 11.

Las semanas son referencias de organización comunicadas por el equipo, no fechas diarias confirmadas. El corte corresponde al 20 de octubre. La fecha exacta de inicio y la equivalencia calendario de las primeras semanas quedan por confirmar; el primer commit conservado es del 2 de septiembre de 2026.

La defensa del 3 o 4 de diciembre es tentativa. Los hitos futuros y sus responsables están sujetos a acuerdo; no existe una línea base aprobada que permita cuantificar retrasos en días.

<!-- page -->

## 1 Hitos y trazabilidad

| Hito y actividad | Sem. | Responsables | Estado | Evidencia y alcance |
|---|---|---|---|---|
| H1 Requerimientos y criterio del 30 % | 1–3 | Todo el equipo | Realizado | Inicio en agosto aproximado; segmentación por nivel y criterio inicial de anotación. |
| H2 Infraestructura y captura V1 | 4–6 | V. Canio / V. Vilches | Realizado | Docker/CVAT e inventarios; 37 originales y 72 variantes sintéticas. |
| H3 Etiquetado V1 y panel YOLO | 7–9 | V. Canio / P. Guerra | Realizado | 91 fotos activas; ensayos YOLO11/26 V1 y demo conservados del 15 de octubre. |
| H4 Desarrollo de detección de bordes | 9–11 | Equipo | Experimental operativo | Inicio en semana 9 informado por el equipo; script y revisiones conservados. |
| H5 Captura y partición V2 | 10 | Todo el equipo | Preparación realizada | 236 imágenes base y 60 con obstáculos; corrección de tareas 20/21 en tarea 22. |
| H6 Integración YOLO y detección de bordes | 11 | Equipo | Experimental operativo | Integración en semana 11 informada por el equipo; panel, adaptador y mapas de señal. |
| H7 Modelos V2 base e informe | 11 | Todo el equipo | Realizado | Dos ensayos V2 base; métricas, informe y entrega Lite con detección de bordes. |
| H8 Revisión de oclusiones y V2 de 3 estados | 12–13 | P. Guerra / V. Vilches | Propuesto pendiente | Cerrar la revisión de etiquetas de la tarea 22 y entrenar; no se declara completado. |
| H9 Deduplicación y refuerzo de faltantes | 14–15 | V. Canio / P. Guerra | Propuesto pendiente | Comparar posprocesamiento en val y ampliar casos reales sin usar test para ajustar. |
| H10 Evaluación final y prueba en otro PC | 16 | Todo el equipo | Propuesto pendiente | Separar test real/sintético/V1 y comprobar instalación de Walmart Visión en otro equipo físico. |
| H11 Documentación y defensa | 17 | Todo el equipo | Propuesto pendiente | Cierre documental y demostración; fecha sujeta a confirmación académica. |

Los rangos semanales históricos se reconstruyen con el equipo y la tabla de referencia; los artefactos permiten verificar resultados, pero no fijan por sí solos la fecha de inicio de cada actividad. El desarrollo de bordes es experimental y su integración no valida un porcentaje real de ocupación.

El hito H5 indica preparación del lote y su partición. La corrección de tareas 20/21 en la 22 no cierra la aprobación final de las etiquetas ni acredita un entrenamiento de tres estados. La validación de Walmart Visión en otro computador sigue pendiente aunque la demo ya esté publicada.

<!-- page -->

## 1 Metodología de trabajo y riesgos

Trabajamos con un enfoque ágil e iterativo inspirado en principios de Scrum. El equipo mantuvo dos reuniones semanales para revisar avances, revisar nuevas imágenes para anotar, discutir diferencias de etiquetado, ajustar criterios y proponer ideas y mejoras. Los acuerdos orientaron el siguiente ciclo de trabajo y permitieron adaptar los datos y los componentes a los resultados observados.

Esta descripción recoge prácticas de inspección y adaptación. Con la información disponible no se atribuyen roles formales, sprints definidos ni una ejecución completa de los eventos de Scrum. Las dos reuniones semanales se describen como seguimiento del equipo; su frecuencia por sí sola no acredita Scrum formal.

Referencia metodológica: Guía Scrum 2020 de Ken Schwaber y Jeff Sutherland, https://scrumguides.org/scrum-guide.html. Para reforzar la trazabilidad se propone registrar fecha, participantes, avances, acuerdos y pendientes de cada reunión.

| Riesgo o dificultad | Evidencia y acción prioritaria |
|---|---|
| Pocos faltantes reales | V2 val contiene un nivel reponer. Capturar escenas reales adicionales y separarlas por escena y sesión. |
| Oclusiones sin validar | V2 base no aprende no_evaluable. Cerrar tarea 22 y medir los tres estados por separado. |
| Etiquetado parcial y duplicados | Revisar la región evaluada y las etiquetas; probar el filtro de duplicados en validación, sin ajustar con la prueba final. |
| Diferencias entre copias | Tarea 19 registra 1.229 niveles en un registro antiguo y 1.212 en la exportación usada. Identificar la versión y su copia fija. |
| Bordes en producto claro y fondo metálico | La nueva selección muestra señal insuficiente sobre envases blancos y señal espuria sobre metal. Comparar ambos con etiquetas de referencia. |
| Réplica y aceptación externa | La demo está disponible, pero falta comprobar la instalación en otro computador físico y ampliar validación. |

El cambio de dimensiones de imágenes de oclusión motivó sustituir las tareas 20/21 por la 22. Se conservan registros de corrección; falta cerrar la aprobación semántica. No se atribuye un retraso en días sin una planificación anterior verificable.

<!-- page -->

## 2 Documentación técnica de la solución

El objetivo es dibujar el espacio completo de cada nivel y clasificar su disponibilidad. V1 distingue vacío, baja disponibilidad, suficiente y no evaluable. V2 base reúne vacío y baja en reponer; V2 completo deberá añadir no_evaluable para situaciones donde un obstáculo impide decidir.

![Arquitectura y flujo](Evidencias/arquitectura_20261020.png)

**Preparar y entrenar:** reunimos fotos, dibujamos contornos y estados en CVAT, revisamos las etiquetas y separamos los datos. Después exportamos esos ejemplos al formato de YOLO y entrenamos. Guardamos los pesos del modelo junto con la configuración y los resultados.

**Analizar una fotografía:** el usuario carga una imagen en el panel. El programa corrige su orientación, ejecuta YOLO y muestra los niveles numerados, sus estados y alertas. Este proceso se llama inferencia. Los números se ordenan de abajo hacia arriba y de izquierda a derecha.

**Revisar bordes:** un análisis opcional estudia cambios de intensidad, color y textura dentro de las máscaras. Se aplica sobre la fotografía original, antes de dibujar los colores del resultado. Permite estudiar dónde aparece la señal y sus errores; no cambia el estado decidido por YOLO ni mide todavía el porcentaje real de productos.

La confianza de una predicción es una puntuación del modelo, no el porcentaje de ocupación de la repisa. Tampoco informa cuántas unidades hay detrás de la primera fila ni las existencias de bodega.

<!-- page -->

## 2 Tecnologías y decisiones

| Tecnología o decisión | Función en el proyecto | Motivo y límite |
|---|---|---|
| Polígonos por nivel completo | Las personas dibujan la repisa incluyendo producto y vacío. | Queremos decidir reposición por nivel. Contar cada tipo de producto, o SKU, exigiría otras etiquetas y un catálogo. |
| YOLO11n y YOLO26n de segmentación | Dibujan los niveles y predicen sus estados. | Comparamos dos variantes Nano con los mismos datos dentro de cada versión. Guardamos pesos y resultados; el tamaño del archivo no demuestra consumo máximo de memoria. |
| PyTorch y Ultralytics | Ejecutan aprendizaje y análisis con YOLO. | Partimos de pesos generales ya entrenados y los adaptamos a nuestras góndolas. Versiones del ensayo: PyTorch 2.5.1+cu121 y Ultralytics 8.4.174. |
| CVAT | Permite dibujar, compartir y revisar etiquetas. | Las etiquetas enseñan al modelo qué contorno y estado esperamos. Una huella SHA-256 comprueba que el archivo no cambió, no que el dibujo sea correcto. |
| Familias y grupos de imágenes | Mantienen relacionadas la foto original y sus variantes. | Evitamos entrenar con una imagen y evaluar con una versión casi idéntica. Esta separación no prueba funcionamiento en otras tiendas. |
| OpenCV, Pillow, NumPy y Shapely | Orientan fotos y trabajan con píxeles, máscaras y formas. | Permiten preparar las imágenes y comprobar las regiones que importamos, exportamos o analizamos. |
| Bordes Canny, color y textura | Añaden mapas de señal dentro de las máscaras YOLO. | Trabajo iniciado en semana 9 e integrado en semana 11. Sirve para experimentar; fondos con textura y carteles aún pueden confundirlo. |
| Docker y panel local | Preparan servicios y permiten operar desde una interfaz. | Facilitan compartir la configuración. Los datos, pesos y accesos a CVAT se preparan aparte. |

En V2 base usamos tamaño de entrada imgsz 640; batch 2, es decir, dos imágenes por paso; seed 42 como semilla para repetir condiciones; optimizador AdamW; y paciencia 20 para detener el entrenamiento si no mejora durante ese número de épocas. Una época es un recorrido de los datos de entrenamiento.

Los ajustes quedan en args.yaml y entorno.json. En nuestro análisis adicional conservamos predicciones con confianza mínima 0,25 y asociamos cada máscara con una referencia una sola vez si su IoU alcanza 0,50. La sección de lectura de resultados explica esa coincidencia de contornos. Estos conteos no utilizan exactamente el mismo procedimiento que el mAP de Ultralytics.

<!-- page -->

## 2 Datos y preparación

| Procedencia | Reales | Sintéticas | Uso y preparación |
|---|---:|---:|---|
| V1 Lider y reserva | 37 | 0 | 30 de desarrollo y 7 reservadas |
| V1 variantes | 0 | 72 | 102 candidatas al sumar 30 reales; 11 exclusiones; 91 activas |
| V2 Líder Express | 59 | 177 | 59 familias con original y tres variantes; tarea 19 |
| V2 visibilidad limitada | 0 | 60 | Ediciones con 24 carros, 24 personas y 12 cajas; tarea 22 |
| Total único | 96 | 309 | 405 imágenes; los 435 registros incluyen referencias repetidas |

Las fotos reales fueron tomadas por el equipo en supermercado. Las variantes IA son ediciones de esas fotos, no capturas nuevas independientes. Una familia reúne una original y sus variantes. Los inventarios guardan su origen, tamaño y huella SHA-256 para comprobar cambios. En V1 excluimos imágenes por problemas de calidad; en V2 las variantes se revisan con una guía común. Sus nombres A/B/C no indican qué estado deben recibir.

**Anotación usada por los modelos:** V1 contiene 719 niveles, con 683 en train y 36 en val. La copia V2 base contiene 1.212 niveles: 816 en entrenamiento, 51 en validación real, 153 en diagnóstico sintético y 192 en reserva. Un registro anterior de tarea 19 contiene 1.229; no se suman ambas versiones.

| Destino V2 base | Originales reales | Variantes IA | Aplicación |
|---|---:|---:|---|
| Entrenamiento | 40 | 120 | 160 imágenes usadas para aprender |
| Validación | 10 | 30 | Métrica principal solo en 10 reales; 30 de diagnóstico separado |
| Prueba final | 9 | 27 | Reservadas; no usadas aquí para elegir modelos |

Distribuimos 19 grupos de imágenes relacionadas: 14 para aprender, 3 para comparar modelos y 2 para la prueba final. Una original y sus variantes van juntas para evitar que aparezcan imágenes casi iguales en entrenamiento y evaluación. Por eso hay menos escenas independientes que archivos. El verificador comprueba esta separación, sin demostrar independencia física total entre escenas.

El lote de oclusiones tiene 308 polígonos, pero hay copias guardadas con repartos de estados distintos. La revisión del 19 de octubre a las 22:27 UTC registra 256 suficientes, 41 no evaluables y 11 reponer; el registro de partición conserva otra copia de 299/9/0. Hasta cerrar la revisión no se adopta un conteo de clases definitivo.

Para la siguiente etapa se reservan 41 imágenes con obstáculos para train, 10 para val y 9 para test. Solo las aprobadas se incorporarán. Al fusionar, el entrenamiento sería 201 imágenes; la validación principal tendría 10 reales más 10 sintéticas de obstáculos, con métricas separadas. Las 30 variantes A/B/C de diagnóstico mantienen su función auxiliar. No se reportará una métrica agregada de 50 imágenes como si fueran 50 fotos reales.


<!-- page -->

## 3 Resultados preliminares de YOLO y bordes

La selección aportada por el equipo utiliza V2-YOLO26 con análisis de bordes, color y textura. Las fichas comparan entrada, salida YOLO y mapa de señal. Se presentan diez ejemplos del grupo favorable y diez de errores, resumidos de dos en dos por página. El caso B09 reemplaza una imagen repetida y pertenece al diagnóstico sintético V2; su captura no identifica el peso exacto. Un resultado favorable puede conservar límites, indicados en su explicación.

El criterio es visual: contornos, estado esperado y ubicación de la señal. No contamos con referencias y registros completos para calcular precisión global o error de ocupación de esta selección. Los porcentajes son señales experimentales: se cita si proceden de una tabla o del propio mapa. Salvo B09, no se infiere su pertenencia a entrenamiento, validación o prueba final.

Las tablas de alimento para mascotas y aceites panorámicos contradicen las imágenes y quedan excluidas de los conteos. También se corrigieron nombres de productos. No se atribuyen causas demostradas a iluminación, perspectiva o reflejos a partir de una sola fotografía.

### Antecedentes cuantitativos de YOLO

Los siguientes valores pertenecen a los ensayos originales del 20 de octubre. No son una evaluación nueva del método combinado ni se mezclan con la selección visual.

| Modelo | mAP50 máscara |mAP50–95 máscara | Localizados | Estado exacto | Extras | Alertas acertadas | Falsas alertas |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLO11-1 | 74,47 % | 56,59 % | 35/36 | 33/36 | 12 | 0/0 | 2 |
| YOLO26-1 | 73,38 % | 62,40 % | 35/36 | 34/36 | 11 | 0/0 | 0 |
| v2_base_yolo11n_01 | 98,44 % | 86,26 % | 51/51 | 48/51 | 8 | 1/1 | 4 |
| v2_base_yolo26n_01 | 99,28 % | 92,79 % | 50/51 | 50/51 | 5 | 1/1 | 0 |

Fuentes: metricas_validacion.json, metricas_alertas.json y evaluacion_por_imagen.json de los ensayos. V1 usa cinco fotos reales; V2 base diez. El 1/1 de alertas V2 es un único faltante. Las métricas no demuestran funcionamiento general en otras tiendas.

IoU mide coincidencia de contornos. mAP50 usa IoU 0,50 y mAP50–95 promedia umbrales de 0,50 a 0,95. No representan el porcentaje de fotos correctas ni el porcentaje real de producto.

<!-- page -->

## 3A Casos favorables

### B01 Bebidas oscuras

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B01 original](Evidencias/casos_yolo_bordes_20261021/B01_original.jpg) | ![B01 yolo](Evidencias/casos_yolo_bordes_20261021/B01_yolo.jpg) | ![B01 bordes](Evidencias/casos_yolo_bordes_20261021/B01_bordes.jpg) |

Esperamos delimitar las repisas y distinguir el hueco parcial inferior. YOLO recupera los niveles visibles y la señal deja parte del hueco sin marcar.

Criterio visual: los contornos siguen las repisas y la señal se concentra principalmente sobre las botellas. El hueco parcial no implica por sí solo un estado reponer.

### B02 Conservas en varios niveles

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B02 original](Evidencias/casos_yolo_bordes_20261021/B02_original.jpg) | ![B02 yolo](Evidencias/casos_yolo_bordes_20261021/B02_yolo.jpg) | ![B02 bordes](Evidencias/casos_yolo_bordes_20261021/B02_bordes.jpg) |

Esperamos separar las repisas con latas. YOLO distingue los niveles y el mapa de bordes mantiene señal sobre gran parte de los productos.

Criterio visual: separación entre niveles y continuidad sobre las latas. Una referencia manual permitiría medir el ajuste de los contornos.

<!-- page -->

## 3A Casos favorables

### B03 Productos en bolsas

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B03 original](Evidencias/casos_yolo_bordes_20261021/B03_original.jpg) | ![B03 yolo](Evidencias/casos_yolo_bordes_20261021/B03_yolo.jpg) | ![B03 bordes](Evidencias/casos_yolo_bordes_20261021/B03_bordes.jpg) |

Esperamos identificar las repisas con bolsas y sus espacios libres. Los contornos permanecen separados y la señal responde a los empaques con dibujos y textura.

Criterio visual: correspondencia entre los grupos de producto y la señal. Es una observación de esta foto, no una garantía para todos los envases.

### B04 Botellas de vidrio

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B04 original](Evidencias/casos_yolo_bordes_20261021/B04_original.jpg) | ![B04 yolo](Evidencias/casos_yolo_bordes_20261021/B04_yolo.jpg) | ![B04 bordes](Evidencias/casos_yolo_bordes_20261021/B04_bordes.jpg) |

Esperamos separar las repisas de botellas. YOLO mantiene los contornos por nivel y el mapa responde sobre buena parte de los envases.

Criterio visual: niveles separados y señal ubicada principalmente en producto. Los reflejos presentes no impiden este resultado; falta comprobar más escenas con reflejos.

<!-- page -->

## 3A Casos favorables

### B05 Conservas en exhibición

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B05 original](Evidencias/casos_yolo_bordes_20261021/B05_original.jpg) | ![B05 yolo](Evidencias/casos_yolo_bordes_20261021/B05_yolo.jpg) | ![B05 bordes](Evidencias/casos_yolo_bordes_20261021/B05_bordes.jpg) |

Esperamos delimitar las filas de conservas sin unir repisas vecinas. La salida de YOLO mantiene los niveles y el mapa muestra señal continua sobre las latas.

Criterio visual: coherencia entre contornos, producto visible y señal. Falta una referencia manual para medir qué parte del área marcada es correcta.

### B06 Vinos con dos repisas casi vacías

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B06 original](Evidencias/casos_yolo_bordes_20261021/B06_original.jpg) | ![B06 yolo](Evidencias/casos_yolo_bordes_20261021/B06_yolo.jpg) | ![B06 bordes](Evidencias/casos_yolo_bordes_20261021/B06_bordes.jpg) |

Esperamos avisar reposición en las dos repisas casi vacías. YOLO las marca reponer y el mapa muestra mucha menos señal que en los niveles abastecidos.

Criterio visual: concordancia en esos dos niveles. La tabla recibida consigna 6,02 % y 2,15 % de señal de área; son valores reportados, no porcentajes reales de inventario.

<!-- page -->

## 3A Casos favorables

### B07 Snacks con faltantes visibles

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B07 original](Evidencias/casos_yolo_bordes_20261021/B07_original.jpg) | ![B07 yolo](Evidencias/casos_yolo_bordes_20261021/B07_yolo.jpg) | ![B07 bordes](Evidencias/casos_yolo_bordes_20261021/B07_bordes.jpg) |

Esperamos distinguir un nivel vacío y otro con pocos productos. YOLO marca reponer en ambos y la señal se concentra en los sectores con bolsas.

Criterio visual: diferenciación entre repisas abastecidas, huecos y faltantes. El documento consigna 2,74 % de señal de área en el nivel vacío; falta calibración contra una referencia.

### B08 Bebidas en exhibidor central

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B08 original](Evidencias/casos_yolo_bordes_20261021/B08_original.jpg) | ![B08 yolo](Evidencias/casos_yolo_bordes_20261021/B08_yolo.jpg) | ![B08 bordes](Evidencias/casos_yolo_bordes_20261021/B08_bordes.jpg) |

Esperamos separar las cuatro repisas del exhibidor. La salida muestra sus contornos y una señal amplia donde están las botellas.

Criterio visual: separación de las cuatro repisas sin incluir todo el pasillo; la señal se concentra principalmente sobre los envases.

<!-- page -->

## 3A Casos favorables

### B09 Cuidado capilar con dos repisas vacías

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B09 original](Evidencias/casos_yolo_bordes_20261021/B09_original.jpg) | ![B09 yolo](Evidencias/casos_yolo_bordes_20261021/B09_yolo.jpg) | ![B09 bordes](Evidencias/casos_yolo_bordes_20261021/B09_bordes.jpg) |

Entrada sintética de diagnóstico: seis repisas, dos vacías. YOLO dibuja las seis y marca reponer en las dos vacías. Los bordes se concentran en cajas y etiquetas; el mapa deja poca señal en el vacío.

Criterio: coherencia entre contornos, estados y señal. El mapa indica 0 % y 2 % de área con señal en las repisas vacías, frente a 62,5–95,5 % en las abastecidas. No equivale a ocupación real ni a una prueba independiente.

### B10 Cervezas en cajas

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![B10 original](Evidencias/casos_yolo_bordes_20261021/B10_original.jpg) | ![B10 yolo](Evidencias/casos_yolo_bordes_20261021/B10_yolo.jpg) | ![B10 bordes](Evidencias/casos_yolo_bordes_20261021/B10_bordes.jpg) |

Esperamos localizar los niveles del módulo con cajas. La salida recupera varios niveles y la señal se concentra en las zonas abastecidas.

Criterio visual: correspondencia favorable en los niveles dibujados. El estante vacío superior requiere revisar cobertura; este ejemplo no acredita detección completa del mueble.

<!-- page -->

## 3B Casos con errores

### F01 Fondo metálico en una repisa vacía

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F01 original](Evidencias/casos_yolo_bordes_20261021/F01_original.jpg) | ![F01 yolo](Evidencias/casos_yolo_bordes_20261021/F01_yolo.jpg) | ![F01 bordes](Evidencias/casos_yolo_bordes_20261021/F01_bordes.jpg) |

Esperamos poca señal en la repisa vacía, pero el mapa marca parte del fondo. La tabla recibida consigna 39,11 % de área con señal.

Posible causa: textura y perforaciones del metal. Mejora: comparar repisas vacías y ocupadas y ajustar el rechazo de fondo sin perder producto oscuro.

### F02 Toallitas claras y fondo vacío

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F02 original](Evidencias/casos_yolo_bordes_20261021/F02_original.jpg) | ![F02 yolo](Evidencias/casos_yolo_bordes_20261021/F02_yolo.jpg) | ![F02 bordes](Evidencias/casos_yolo_bordes_20261021/F02_bordes.jpg) |

Esperamos señal en los paquetes y poca en el vacío. El mapa deja producto claro poco marcado y activa sectores del fondo; la tabla reporta 32,03 % de área en el nivel señalado como vacío.

Posible causa: poco contraste y textura del fondo. Mejora: evaluar colores claros y fondos por separado antes de cambiar los umbrales.

<!-- page -->

## 3B Casos con errores

### F03 Nivel omitido en alimento para mascotas

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F03 original](Evidencias/casos_yolo_bordes_20261021/F03_original.jpg) | ![F03 yolo](Evidencias/casos_yolo_bordes_20261021/F03_yolo.jpg) | ![F03 bordes](Evidencias/casos_yolo_bordes_20261021/F03_bordes.jpg) |

Esperamos los cuatro niveles físicos. La imagen de YOLO muestra tres contornos y deja una repisa intermedia sin delimitar; bordes no puede analizar un nivel que no recibe.

Posible causa: sombra o similitud entre filas. Mejora: revisar la etiqueta del nivel y repetir con el registro original. La tabla recibida tiene seis filas incompatibles; no se calcula recall con ella.

### F04 Aceites en una toma panorámica

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F04 original](Evidencias/casos_yolo_bordes_20261021/F04_original.jpg) | ![F04 yolo](Evidencias/casos_yolo_bordes_20261021/F04_yolo.jpg) | ![F04 bordes](Evidencias/casos_yolo_bordes_20261021/F04_bordes.jpg) |

Esperamos cubrir los niveles visibles del sector. La salida dibuja solo dos regiones y deja repisas intermedias sin analizar; un carro ocupa el primer plano.

Posible causa: encuadre amplio, escala y obstáculos. Mejora: comparar una captura frontal más cercana. La tabla recibida tiene siete filas y se excluye del conteo hasta cotejarla.

<!-- page -->

## 3B Casos con errores

### F05 Contorno que incluye un exhibidor lateral

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F05 original](Evidencias/casos_yolo_bordes_20261021/F05_original.jpg) | ![F05 yolo](Evidencias/casos_yolo_bordes_20261021/F05_yolo.jpg) | ![F05 bordes](Evidencias/casos_yolo_bordes_20261021/F05_bordes.jpg) |

Esperamos analizar solo la repisa. Un contorno alcanza productos colgados a la derecha y la señal puede incorporar material ajeno al nivel.

Posible causa: límites laterales ambiguos. Mejora: revisar el contorno de referencia y probar un recorte por módulo, comprobando que no elimine producto válido.

### F06 Acopio superior y límites del mueble

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F06 original](Evidencias/casos_yolo_bordes_20261021/F06_original.jpg) | ![F06 yolo](Evidencias/casos_yolo_bordes_20261021/F06_yolo.jpg) | ![F06 bordes](Evidencias/casos_yolo_bordes_20261021/F06_bordes.jpg) |

La salida delimita las repisas interiores y deja el área superior de acopio sin analizar. También hay productos laterales que requieren revisar el límite de evaluación.

Posible causa: alcance de etiquetado distinto al esperado. Mejora: acordar si el acopio superior pertenece al problema y etiquetarlo de forma consistente antes de llamarlo omisión.

<!-- page -->

## 3B Casos con errores

### F07 Azúcar en envases blancos

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F07 original](Evidencias/casos_yolo_bordes_20261021/F07_original.jpg) | ![F07 yolo](Evidencias/casos_yolo_bordes_20261021/F07_yolo.jpg) | ![F07 bordes](Evidencias/casos_yolo_bordes_20261021/F07_bordes.jpg) |

Esperamos señal sobre los paquetes blancos. YOLO identifica la repisa, pero el mapa deja gran parte de esos productos sin marcar. La tabla consigna solo 13,57 % de señal de área en el nivel revisado.

Posible causa: bajo contraste, color poco saturado o respuesta insuficiente de textura. Mejora: añadir controles de envases blancos sin aumentar falsas activaciones en repisas vacías.

### F08 Sal en bolsas blancas

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F08 original](Evidencias/casos_yolo_bordes_20261021/F08_original.jpg) | ![F08 yolo](Evidencias/casos_yolo_bordes_20261021/F08_yolo.jpg) | ![F08 bordes](Evidencias/casos_yolo_bordes_20261021/F08_bordes.jpg) |

Esperamos señal donde se apilan bolsas. El mapa apenas responde en algunas repisas abastecidas; el documento reporta 5,64 % y 0 % de señal de área.

Posible causa: envases lisos y claros. Mejora: comparar producto y fondo con etiquetas manuales. Un 0 % de señal no significa que no haya producto.

<!-- page -->

## 3B Casos con errores

### F09 Recargas flexibles en la parte superior

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F09 original](Evidencias/casos_yolo_bordes_20261021/F09_original.jpg) | ![F09 yolo](Evidencias/casos_yolo_bordes_20261021/F09_yolo.jpg) | ![F09 bordes](Evidencias/casos_yolo_bordes_20261021/F09_bordes.jpg) |

Esperamos cubrir las repisas acordadas, incluida la superior si está dentro del alcance. La salida omite la fila de recargas y delimita principalmente las botellas inferiores.

Posible causa: forma y posición diferentes de los empaques. Mejora: revisar cobertura de las etiquetas y añadir ejemplos de recargas flexibles en la parte superior.

### F10 Leche en polvo y una detección en el techo

| Original | Resultado YOLO | Señal de bordes |
|---|---|---|
| ![F10 original](Evidencias/casos_yolo_bordes_20261021/F10_original.jpg) | ![F10 yolo](Evidencias/casos_yolo_bordes_20261021/F10_yolo.jpg) | ![F10 bordes](Evidencias/casos_yolo_bordes_20261021/F10_bordes.jpg) |

Esperamos contornos solo sobre repisas. YOLO también dibuja un nivel en el techo. Hay un hueco parcial que exige revisar el estado esperado con el criterio de ancho acordado.

Posible causa: líneas del techo parecidas a una repisa. Mejora: delimitar la región del mueble y revisar la referencia. No se cambia a reponer solo por señal baja ni por tener un hueco parcial.

<!-- page -->

## 3C Análisis comparativo y mejoras

Los ejemplos favorables muestran que YOLO puede separar repisas y que el mapa de bordes responde sobre productos con contraste o textura. Vinos y snacks permiten observar diferencias entre sectores abastecidos y vacíos. Estos ejemplos no establecen una distancia o un ángulo de captura óptimos ni una mejora de precisión respecto de YOLO solo.

| Patrón observado | Casos de referencia | Acción prioritaria |
|---|---|---|
| Poco marcado de producto blanco o liso | F02, F07 y F08 | Etiquetar producto y fondo; comparar señales con distintos materiales e iluminación. |
| Señal sobre metal sin producto | F01 y F02 | Preparar controles de repisa vacía y ajustar rechazo de fondo sin perder producto oscuro. |
| Repisas omitidas o fuera del alcance | F03, F04, F06 y F09 | Revisar etiquetas, alcance del acopio y registros de ejecución; comparar capturas frontales y amplias. |
| Contorno que invade otra región | F05 y F10 | Delimitar el mueble y probar recortes sin eliminar repisas válidas. |

Las causas propuestas son hipótesis. Para comprobarlas hay que cambiar un aspecto a la vez, registrar la configuración y comparar con referencias humanas. Las tablas que no coinciden con las imágenes deben cotejarse con la salida original antes de calcular tasas de error. No se incorporaron nuevas inferencias ni se utilizó la reserva final para esta revisión.

No se propone convertir automáticamente una señal baja en alerta: azúcar y sal muestran que puede haber producto con señal muy baja. Tampoco basta un hueco parcial para declarar reponer; debe revisarse el criterio de ancho del 30 % y acordar su calibración. Las reglas de fusión se evaluarían después de validar ambas salidas.

El documento recibido incluye tiempos por foto, pero no identifica de forma suficiente hardware, calentamiento y tramo medido. No se presentan como latencia reproducible. La siguiente evaluación deberá registrar captura, modelo y peso exactos, ajustes, regiones, etiquetas esperadas y tiempo completo hasta mostrar el resultado.

<!-- page -->

## 4 Repositorio y reproducibilidad

La carpeta local organiza código en Herramientas, datos y versiones en Datos, resultados en Experimentos, configuración en Infraestructura y documentación en Documentacion. El README local describe decisiones, arquitectura, datasets, estado e instrucciones.

Repositorio de referencia: https://github.com/vcanio/Capstone2026. El historial Git conserva un primer commit del 2 de septiembre de 2026; el inicio aproximado en agosto procede del relato del equipo. La primera consulta del 20 de octubre describía un estado anterior y no representa la publicación actual. Su respuesta completa queda solo en local; el [resumen público de la consulta](Evidencias/README.md#consulta-histórica-de-github) conserva el alcance de ese registro.

La entrega actual es Walmart Visión: https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-docker-2026-10-21. Incluye cuatro modelos y bordes; en Windows usa iniciador local y en Mac ofrece Docker. La Release permite probar fotografías propias y no contiene el dataset ni el informe. El laboratorio requiere los paquetes del equipo, instalados con --assets. La guía de usuario y las instrucciones Docker explican la réplica.

Desde la raíz, con Python 3.11 o 3.12 y los datos/modelos necesarios disponibles:

```powershell
python -m venv .venv-modelo
& ./.venv-modelo/Scripts/python.exe -m pip install -r Herramientas/Modelos/requirements.txt
& ./Herramientas/Modelos/iniciar_panel.ps1 -Cpu -Build
# GPU NVIDIA: omitir -Cpu con entorno Docker/GPU configurado
& ./.venv-modelo/Scripts/python.exe Herramientas/verificar_proyecto.py
& ./.venv-modelo/Scripts/python.exe Herramientas/Datos/particionar_lider_express.py --verify
```

Abrir http://localhost:8090, seleccionar V2 y v2_base_yolo26n_01, cargar la foto lider_express_040_0_original y analizar. La evaluación guardada a conf 0,25 contiene cinco niveles, cuatro suficientes y uno reponer. La demostración debe comparar contra esa configuración y referencia. Una foto propia sin etiqueta permite observar una predicción, no calcular precisión.

Walmart Visión incluye los cuatro modelos V1/V2 y detección de bordes. El primer inicio prepara dependencias o la imagen Docker. Las comprobaciones en Linux AMD64 y ARM64 emulado no sustituyen una instalación en otro computador físico ni en macOS; esas pruebas siguen pendientes según la documentación de la entrega.

**Verificación al corte:** auditoría correcta de 43 documentos, 270 enlaces locales, 435 registros de imágenes, 2 exportaciones compartidas y 52 archivos Python. Pasaron las 11 pruebas de datos; la suite de modelos terminó correctamente con 222 pruebas y una omitida. La partición de 296 imágenes también pasó. El [registro público](Evidencias/verificacion_informe_20261020.json) conserva los resultados; los logs extensos se guardan solo en local, según la [política de evidencias](Evidencias/README.md). La revisión anterior de planificación quedó registrada en Evidencias/verificacion_planificacion_20261020.json. La revisión de lectura quedó en Evidencias/verificacion_claridad_20261020.json. La selección actual y sus correcciones están en Evidencias/casos_yolo_bordes_20261021.json; su revisión documental se registra por separado. Las pruebas de código no sustituyen una validación del modelo ni una demostración en hardware externo.


<!-- page -->

## 5 Conclusiones y próximos pasos

Logramos preparar imágenes, etiquetarlas, entrenar y comparar modelos, y analizar fotos desde una interfaz local. Conservamos cuatro modelos con resultados e imágenes de comparación y añadimos la revisión visual de YOLO + bordes. V2 base obtiene mejores métricas de contornos en su propia validación, pero cambian los datos y las categorías respecto de V1. La detección de faltantes reales todavía se apoya en pocos ejemplos.

El panel dispone de carga de imágenes, selección de modelo, ejecución de inferencia y visualización de estados. Los artefactos demuestran implementación, mientras que la disponibilidad del despliegue y la ejecución en un equipo limpio necesitan una comprobación adicional. V2 de tres estados, deduplicación validada, prueba final y validación de Walmart Visión en otro computador permanecen pendientes.

| Actividad propuesta | Responsable propuesto | Fecha estimada | Criterio de cierre |
|---|---|---|---|
| Cotejar imágenes, tablas y configuración de los casos | Todo el equipo | 23 oct | Registros asociados a cada imagen y diferencias resueltas |
| Cerrar revisión de 308 polígonos de tarea 22 | Paulo Guerra y Vicente Vilches | 27 oct | Copia de etiquetas aprobada y diferencias resueltas |
| Entrenar y comparar V2 de tres estados | Vicente Canio y Paulo Guerra | 3 nov | Ensayos versionados y métricas por origen/clase |
| Evaluar duplicados, envases claros y fondos | Vicente Canio y Paulo Guerra | 10 nov | Comparación con referencias sin empeorar niveles vecinos |
| Capturar faltantes reales independientes | Vicente Vilches y equipo | 17 nov | Nuevas escenas anotadas y partición versionada |
| Congelar modelo y ejecutar prueba final | Todo el equipo | 26 nov | Prueba real separada de los ejemplos sintéticos |
| Validar Walmart Visión en otro computador físico | Vicente Canio y equipo | 26 nov | Instalación y ejecución externa verificadas; la demo ya está publicada |
| Cerrar informe y preparar defensa | Todo el equipo | 3 o 4 dic | Demostración y documentación consistentes |

Estas asignaciones y fechas son propuestas que el equipo debe acordar. El MVP es la versión mínima necesaria para comprobar la solución. Llegar a tiempo depende de aprobar las etiquetas y reunir más faltantes reales antes de fijar el modelo para la prueba final. El 77,8 % de hitos no autoriza afirmar que resta el 22,2 % del esfuerzo; la captura y validación pueden dominar el tiempo restante.

La evaluación final principal debe separar los nueve originales reales V2 de sus 27 variantes y de las nueve imágenes sintéticas con obstáculos. Las siete fotos reservadas V1 constituyen otro conjunto y deben evaluarse por separado, siempre que no hayan sido usadas para ajustar el método. Si se incorporan nuevas escenas, se crea una versión y se congela su destino antes de consultar resultados. No se combinarán 52 imágenes heterogéneas como una sola prueba real independiente.
