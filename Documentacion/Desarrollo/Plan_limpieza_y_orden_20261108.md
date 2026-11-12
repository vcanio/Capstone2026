# Plan de limpieza y orden del proyecto

Fecha: 8 de noviembre de 2026, Santiago. Estado: **ejecutado con las dependencias conservadas que detalla el [recibo de cierre](Limpieza_orden_20261108.md)**. El diagn?stico y las etapas siguientes conservan el texto de la propuesta original.

Objetivo solicitado por Vicente: dejar a la vista solamente los datos, código y herramientas necesarios para trabajar con la última versión estable; reunir el resto en `Historico/` para documentar el progreso. La propuesta conserva el material existente: archivar no significa borrar ni reconstruir archivos retirados anteriormente.

## 1. Resultado de la revisión

Se inventarió toda la raíz física del proyecto, incluidas carpetas ocultas, entornos, copias de publicación y archivos de Git, sin recorrer junctions ni enlaces simbólicos. Se revisaron los registros vigentes, las instrucciones y antecedentes de limpieza disponibles, los puntos de entrada de aplicación y laboratorio, importaciones de la app, empaquetado, montajes Docker, documentación e índices principales.

- **108.650 archivos, 37,366 GiB lógicos**, antes de crear los documentos de esta revisión.
- **24 enlaces/junctions** registrados aparte; no se sumó su contenido de nuevo ni se recorrió el `node_modules` externo.
- Ningún error al enumerar metadatos. Esto no equivale a leer y validar el contenido de todos los archivos ni a comprobar todos los duplicados por hash.
- Se verificaron por SHA-256 el peso oficial del ensayo, su copia operativa y el ZIP local publicado del 5/11.
- No se movieron ni borraron archivos existentes; no se modificaron código, datos, CVAT, pesos o particiones. No hubo entrenamiento, inferencia ni publicación.

Inventario por archivo, tamaños, agrupaciones y destinos de enlaces: inventario de revisión (`Historico/Evidencias/Temporales/plan_limpieza_20261108/inventario.json`, archivo del entorno local; fuera de esta distribución). Es un registro local; no se propone publicarlo.

| Área | Archivos | GiB lógicos | Lectura para la limpieza |
|---|---:|---:|---|
| Datos | 9.161 | 11,789 | 9,037 GiB son preparaciones; mezcla fuentes vigentes y copias históricas. |
| Laboratorio | 7.717 | 8,459 | 8,219 GiB corresponden a experimentos y sus datasets. |
| .publicacion | 10.577 | 6,004 | Paquetes de desarrollo antiguos, copias y checkouts con relaciones Git. |
| .venv-modelo | 27.724 | 5,037 | Entorno del laboratorio; conservar operativo. |
| Aplicacion | 41.895 | 3,189 | 3,140 GiB están en entorno y runtime; la app también conserva dos pesos anteriores. |
| .tmp | 6.096 | 2,453 | Evidencias, extracciones y trabajos de distintas fechas. |
| Entregables | 39 | 0,250 | Once ZIP V3 entre fechas y subcarpetas, además de informes. |
| .venv-cvat | 3.468 | 0,089 | Entorno técnico de CVAT. |
| Historico | 1.653 | 0,051 | Archivo existente, todavía pequeño frente al material histórico disperso. |
| Documentacion | 164 | 0,019 | Guías vigentes mezcladas con antecedentes y referencias desactualizadas. |
| Modelos | 7 | 0,017 | Acceso al actual y tres preentrenados generales. |

Los tamaños son lógicos; no miden bloques físicos únicos. Mover archivos al histórico dentro del mismo disco **ordena, pero no libera ese espacio**. No se fija una reducción de GB como objetivo de esta operación.

## 2. Qué se considera vigente

La referencia operativa será la aplicación local del **8/11**, incluyendo Línea A y la corrección de contornos, con el modelo oficial adoptado el **5/11**. La distribución publicada queda identificada por separado.

| Componente | Referencia comprobada |
|---|---|
| Aplicación | `Aplicacion/`, revisión `linea_a_20261108_contornos_conservados`. |
| Configuración oficial | `.config-modelo/version_actual_v3.json` y `Aplicacion/modelos.json`. |
| Modelo | `v3_refuerzo_geometria_revision_20261105_022414_e6f0`, `best.pt`. |
| Hash del modelo | `7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a`, igual en ensayo y app. |
| Partición de desarrollo | `Datos/Registros/Particiones/v3_refuerzo_geometria_20261104/particion.json`, señalada por `activa_v3.json`. |
| Preparación | `Datos/Preparados/V3/v3_20261105_012333_53df4a59/`, exportación `exportacion_71b4668d`. |
| Selección | `Datos/Preparados/V3/Selecciones/revision_geometria_20261104/`. |
| Refuerzo y procedencia | `Datos/Preparados/V3/Refuerzos/revision_geometria_20261104/`. |
| Datos efectivos del ensayo | 171 train, 59 validación real y 34 sintética; la preparación contiene 275 imágenes, 264 elegibles y 11 bloqueadas. |
| Ocupación en desarrollo | `Laboratorio/Ocupacion/` y `Datos/Preparados/V3/Calibracion_ocupacion_20261107/`; conservar etiquetas humanas y muestra congelada. |
| Distribución publicada registrada | `Entregables/V3/Walmart_Vision_V3_20261105.zip`, hash `4124744d2615f555280070537ba6308e60025a02729990b3116eda594cc2c3c7`. |

El ZIP del 5/11 conserva el estimador anterior; no representa los cambios locales del 8/11. Ordenar las carpetas no autoriza sobrescribirlo ni actualizar una release. Línea A mantiene índice visual 0–100 y umbral 52, con evaluación preliminar; la limpieza no cambia su grado de validación.

## 3. Estructura propuesta

Conservar los nombres principales actuales evita otra reorganización general innecesaria. Dentro de cada área activa quedará una entrada inequívoca al material vigente.

```text
Walmart/
  README.md                   Accesos y estado local/publicado
  AGENTS.md                   Reglas vigentes y referencias al historial
  Aplicacion/                 App actual, pruebas y único modelo ofrecido
  Laboratorio/                Herramientas actuales y ensayo oficial
  Datos/                      Fuentes usadas, preparación actual y registros necesarios
  Modelos/                    Acceso al modelo vigente y recursos utilizados
  Entregables/                 Última distribución publicada, claramente identificada
  Documentacion/              Guías actuales y acceso a la evolución
  Infraestructura/            Configuración operativa de servicios
  Historico/
    README.md                 Índice por etapa y fecha
    Evolucion.md              Cambios, motivos, resultados y limitaciones
    Experimentos/             Ensayos cerrados anteriores
    Datos/                    Preparaciones y exportaciones sustituidas
    Codigo/                   Herramientas y prototipos retirados del flujo actual
    Entregables/               Paquetes e informes anteriores
    Documentacion/            Guías e informes fechados anteriores
    Evidencias/               Revisiones, pruebas y recibos cerrados
    Publicaciones/            Paquetes y material de publicaciones anteriores
    Contexto/                 Referencias y material académico existentes
    Reproducibilidad/         Registros históricos existentes
  .config-modelo/             Configuración operativa
  .tmp/                       Solo trabajo en curso
  .resguardo/                 Solo protección temporal de operaciones en curso
  .publicacion/               Infraestructura Git protegida, mientras se use
  .venv-modelo/ y .venv-cvat/  Entornos instalados
```

Las carpetas técnicas ocultas, `.github`, `.agents`, archivos de configuración y enlaces necesarios pueden permanecer en la raíz. No es útil convertir entornos instalados en documentación histórica ni romper sus rutas para reducir el número de carpetas.

## 4. Clasificación y destinos concretos

Las rutas son propuestas de ejecución, no movimientos ya realizados. Cada lote necesita verificar referencias antes del traslado.

| Origen | Decisión y destino |
|---|---|
| `Aplicacion/` y sus pruebas, iniciadores, Docker y dependencias locales | Conservar. Incluye `ocupacion_paulo.py`, `ocupacion_linea_a.py`, geometría, presentación y módulos compartidos que todavía se importan. |
| `Aplicacion/modelos/V3-YOLO26.pt` y `V3-segmentacion-candidato-20261102.pt` | Archivar en `Historico/Experimentos/Copias_operativas/`, manteniendo nombre y hash. No están en el manifiesto actual; la búsqueda acotada en código/configuración operativos no encontró referencias a esos nombres. |
| `Laboratorio/Experimentos/v3_refuerzo_geometria_revision_20261105_022414_e6f0/` | Conservar completo como soporte del modelo actual: dataset, manifiesto, configuración, métricas y entrenamiento. No desarmarlo para ahorrar unos MB de checkpoints. |
| `Laboratorio/Experimentos/v3_afinado_papeles_huevos_20261026_011847_7021/` | Archivar completo bajo `Historico/Experimentos/`, conservando identificación del ensayo y resolución de sus rutas. 1,485 GiB. |
| `Laboratorio/Experimentos/v3_segmentacion_sin_tapadas_20261102_202529_4bb3/` | Archivar bajo `Historico/Experimentos/` después de resolver la referencia al padre del modelo oficial. 3,360 GiB. No alterar el `initial_model` del manifiesto congelado para aparentar otra procedencia. |
| `Laboratorio/Experimentos/visibilidad_foto_20261102_163858_5061/` y preparaciones de ese ensayo | Histórico experimental; trasladar después de revisar las rutas de visibilidad que aún importa el panel. No describirlo como capacidad de la app estable. |
| Preparaciones `Datos/Preparados/V3/v3_*` anteriores a la preparación activa | `Historico/Datos/Preparados/V3/`, conservando nombres, exportaciones y manifiestos. No mover la preparación vigente ni asumir que todo lo fechado es descartable. |
| `Datos/Preparados/V3/Pilotos/`, selecciones cerradas y refuerzos de octubre | `Historico/Datos/Preparados/V3/`, después de separar referencias compartidas y preservar el registro del linaje. |
| `Datos/Preparados/V3/Comparacion_modelos_20261105/` | Conservar el informe de comparación accesible desde el modelo actual; archivar los artefactos cerrados en `Historico/Evidencias/` cuando sus lectores ya resuelvan el nuevo destino. |
| `Datos/Registros/Versiones_modelos/` y particiones sustituidas | Archivar únicamente lo que deje de ser dependencia operativa. La fuente activa de CVAT aún cita la partición de 469: no moverla de forma ciega ni modificar su contenido. |
| Fuentes de `Datos/V1`, `Datos/V2`, `Datos/V3` y `Datos/Fuentes` | Clasificar por uso real, no por nombre de versión. Mantener las fuentes y alias necesarios por la selección vigente, calibración, CVAT y reserva final. Archivar solo fuentes exclusivamente históricas cuya trazabilidad quede resuelta. |
| `Laboratorio/Experimentos/Bordes/` | Conservar inicialmente: el laboratorio carga código desde allí. Separar después núcleo compartido y evidencias antiguas; cualquier traslado de código requiere actualizar importaciones y pruebas. |
| `Laboratorio/Ocupacion/` | Conservar: es trabajo vigente de evaluación/calibración, no residuo. Mantener el prototipo separado de la implementación portable de la app. |
| Scripts de operaciones puntuales ya cerradas en `Laboratorio/Modelos/` | Candidatos a `Historico/Codigo/Operaciones/`: revisiones, restauración y orden de CVAT fechadas. Confirmar que no sean importados por herramientas o pruebas vigentes antes de moverlos. |
| `Laboratorio/Experimentos/panel_pruebas/` | Separar estados vigentes y fotos originales subidas de ejecuciones cerradas. Archivar las cerradas bajo `Historico/Evidencias/Panel/`; conservar las fotos y los recibos citados. No vaciarlo completo. |
| ZIP y subcarpetas de entrega del 25–28/10 | `Historico/Entregables/V3/` conservando nombres, subcarpetas y SHA. Mantener el ZIP publicado del 5/11 en `Entregables/V3/`. |
| Informes intermedios, guiones y material de demo anterior | `Historico/Documentacion/` o `Historico/Entregables/`, enlazados por etapa. Conservar los originales académicos y sus formatos; respetar ubicaciones protegidas de Fase 1/Fase 2. |
| `.publicacion/paquetes_desarrollo/` | Candidato a `Historico/Publicaciones/paquetes_desarrollo/`: 2,878 GiB. Verificar referencias locales antes de mover. |
| Recibos cerrados en `.publicacion`, `.resguardo` y `.tmp` | `Historico/Evidencias/<fecha_y_operacion>/`, con mapa de rutas y enlaces corregidos. Los recibos recientes de Línea A y contornos deben seguir accesibles desde la documentación actual. |
| Extracciones e instancias antiguas de `.tmp` | `Historico/Entregables/Instancias_prueba/` cuando se confirme que ningún proceso las usa. Conservar material original de video y pruebas, no tratarlo todo como caché. |
| `.publicacion/repositorio` y worktree asociado | Mantener intactos en esta limpieza ordinaria; indexarlos desde Histórico. Una migración física eventual requiere un lote especial de Git y reparación/verificación de worktrees. |
| `.venv-modelo`, `.venv-cvat`, `Aplicacion/.entorno-py312` y runtime Python | Conservar. El iniciador de la app depende de esas ubicaciones; GPU/laboratorio y CPU/app no son entornos intercambiables sin comprobación. |
| `Aplicacion/.runtime/cache`, `__pycache__` y cachés de herramientas | Separar caché regenerable de intérpretes, sesiones y evidencias. Esta propuesta no incluye borrado: cualquier purga para recuperar espacio sería una acción explícita distinta. |
| `Modelos/preentrenados/` | Clasificar los tres pesos por referencias de código y experimentos. Conservar los requeridos por herramientas actuales; los exclusivos de experimentos cerrados pueden pasar a `Historico/Experimentos/Recursos/`. |

## 5. Dependencias y problemas encontrados

1. **Nombres de versión no equivalen a desuso.** La muestra de ocupación del 7/11 todavía contiene rutas `Datos/V2/lider_express_20261016/...`. Esas rutas son enlaces a fuentes físicas V3. El refuerzo vigente también guarda originales bajo `Preparados/Refuerzos/`; no es solo una copia prescindible.
2. **El estado documental está mezclado.** `Mapa_del_proyecto.md`, `Datos/README.md`, `Datos/Preparados/V3/README.md`, `Laboratorio/Experimentos/README.md` y partes de `estado_actual.json` describen todavía el afinado de octubre. `Documentacion/Estado_V3_actual.json` tiene el modelo del 5/11, pero conserva el umbral 30 del estimador publicado. Corregir las vistas actuales y conservar los documentos fechados como historia, identificando app local y release por separado.
3. **Los manifiestos tienen hashes y rutas congeladas.** No hacer reemplazos masivos de texto dentro de ellos. Crear un mapa de ubicación actual por ID histórico y adaptar los lectores. Usar junctions de compatibilidad solo donde hagan falta y registrar su destino; Docker necesita montajes o resolución propios, no depender de enlaces de Windows.
4. **Hay un worktree real.** `.publicacion/vision_ocupacion_20261022/source/.git` apunta a `.publicacion/repositorio/.git/worktrees/source`. Mover carpetas de publicación por arrastre rompería esa relación. La consulta Git local confirmó ambos; el estado de archivos rastreados del checkout principal no mostró cambios, pero no se auditó todo lo no rastreado ni se consultó GitHub.
5. **Faltan recibos de limpiezas anteriores.** Los README de `.resguardo/reorganizacion_20261026/` y `.resguardo/aligerado_20261026/` ya no existen. No reconstruir respaldos retirados ni presentar sus verificaciones como disponibles.
6. **Persisten tres fuentes V1 ausentes.** `Datos/V1/Lider/lider_001.jpg`, `lider_002.jpg` y `lider_003.jpg`. Registrar como incidencia previa; no restaurarlas, borrarlas del inventario ni afirmar que la auditoría global pasó.
7. **No se confirmó qué servicios están ejecutándose.** La consulta de procesos CIM y las conexiones HTTP locales estaban restringidas en esta sesión. No se interpreta como servicios detenidos; comprobarlo antes de mover instancias o registros de trabajos.
8. **Los verificadores también necesitan revisión de alcance.** El general recorre fuentes con `rglob` y puede alcanzar entornos; el de partición conserva supuestos de versiones previas. Antes de usarlos como criterio de cierre, asegurar que validan la partición activa de esquema 4 sin reclasificar la reserva final ni confundirla con el conjunto de desarrollo.

## 6. Secuencia de ejecución propuesta

### Etapa 1 — Fijar la referencia y preparar movimientos verificables

- Guardar el estado previo de los registros operativos y los hashes del modelo, módulos actuales y paquete publicado.
- Convertir esta clasificación en un manifiesto por lote: origen absoluto, destino absoluto, motivo, número de archivos, tamaño, hash por archivo, referencias afectadas y reversión.
- Comprobar que cada origen/destino resuelto pertenece al proyecto, no atraviesa un enlace externo y no sobrescribe una carpeta existente. Tratar los enlaces como objetos separados.
- Confirmar que no hay entrenamientos, etiquetados, empaquetados o publicaciones escribiendo en los destinos afectados. No detener servicios ajenos ni iniciar entrenamientos.
- Tomar respaldo solo de los pequeños archivos que deban editarse; no duplicar los 37 GiB ni recrear respaldos antiguos.

### Etapa 2 — Archivar material independiente

- Empezar por los dos pesos antiguos de la app, paquetes anteriores, informes cerrados y evidencias sin lectores activos.
- Mover dentro del mismo volumen y conservar los bytes originales; verificar cantidad y hashes inmediatamente después de cada lote.
- No mezclar carpetas con igual nombre procedentes de distintas fechas. Mantener un recibo por movimiento.
- Dejar `.tmp` con trabajo en curso y enlaces de compatibilidad necesarios, después de identificar procesos y consumidores.

### Etapa 3 — Resolver historia y dependencias compartidas

- Archivar ensayos anteriores conservando configuraciones, datasets, métricas, CSV, pesos existentes, decisiones e imágenes de evidencia. Son archivo de consulta, no candidatos del catálogo habitual.
- Mantener el ensayo oficial, su exportación, selección, refuerzo y las etiquetas de ocupación activos.
- Adaptar la resolución de IDs históricos antes de mover preparaciones, particiones o fuentes referenciadas. Un archivo antiguo que aún usa el flujo actual sigue siendo dependencia hasta que se resuelva su migración.
- Separar código compartido de los prototipos/evidencias dentro de `Bordes`; mantener pruebas y comportamiento. Retirar scripts históricos del área activa solo después de revisar importaciones, invocaciones y CI.
- Conservar intactos los metadatos de test; no abrir imágenes, inferir, ajustar umbrales ni volver a repartir escenas.

### Etapa 4 — Hacer que la documentación refleje la estructura final

- Actualizar README principal, mapa, guías de Datos/Modelos/Laboratorio/Entregables y registros de estado actuales usando las referencias oficiales.
- Crear `Historico/Evolucion.md` con etapa, cambio, motivo, datos/partición, métricas, limitaciones y enlaces a evidencia. No comparar como equivalentes métricas de particiones distintas.
- Conservar los documentos fechados; corregir enlaces mediante índices o mapa de traslados sin reescribir los hechos históricos.
- Reducir la repetición en `AGENTS.md` dejando reglas actuales y enlaces a la cronología completa, con copia de su contenido previo en Histórico. Mantener las excepciones y restricciones vigentes.
- Documentar explícitamente la diferencia entre app local del 8/11 y ZIP publicado del 5/11.

### Etapa 5 — Comprobar funcionamiento y cerrar

- Comparar hashes antes/después de fuentes movidas, etiquetas, manifiestos, pesos y ZIP publicado. No basta con contar archivos.
- Ejecutar comprobaciones de importación y las pruebas existentes afectadas: app, Línea A, empaquetador, catálogo, rutas, selección y partición; no entrenar como prueba.
- Comprobar arranque de app y laboratorio, carga del modelo oficial y resolución de las referencias históricas necesarias.
- Generar un paquete temporal nuevo, con nombre distinto al publicado, y verificarlo aislado con dos fotos de desarrollo ya autorizadas o un caso artificial. Comprobar también que Windows y la configuración Docker resuelven las rutas.
- Revisar enlaces de documentación y que el catálogo habitual solo presente el estado operativo esperado. Ninguna consulta histórica debe ser necesaria para iniciar la app estable.
- Emitir recibo final: movimientos reales, incidencias anteriores, resultados de pruebas y pasos de reversión. Si falla un lote, revertir ese lote antes de continuar.

## 7. Criterio de finalización

La limpieza estará terminada cuando se pueda abrir el proyecto y distinguir inmediatamente aplicación, modelo y datos actuales; los ensayos y entregas anteriores estén reunidos e indexados en Histórico; las dependencias técnicas restantes estén justificadas; y las comprobaciones confirmen el mismo comportamiento y los mismos bytes de datos/modelos protegidos.

No se exige eliminar toda carpeta oculta ni que Histórico sea pequeño. Para este objetivo se conserva el material anterior sin borrarlo. Una reducción física adicional de espacio —cachés, duplicados o binarios históricos— requeriría otro alcance, con tamaños y equivalencias comprobados.

## Referencias consultadas

- Registro del modelo oficial (`.config-modelo/version_actual_v3.json`, archivo del entorno local; fuera de esta distribución) y [manifiesto operativo](../../Aplicacion/modelos.json).
- [Modelo oficial del 5/11](Modelo_oficial_V3_20261105.md), [Línea A](../../Aplicacion/Documentacion/LINEA_A_20261108.md) y [conservación de contornos](Correccion_contornos_productos_20261108.md).
- Reorganización del 26/10 (`Historico/Documentacion/Desarrollo/Reorganizacion_carpetas_20261026.md`, archivo del entorno local; fuera de esta distribución), [historial y aligerado](Historial_modelos_y_cambios.md) y limpieza del laboratorio (`Historico/Documentacion/Desarrollo/Limpieza_laboratorio_20261030.md`, archivo del entorno local; fuera de esta distribución).
- [Partición activa](../Estado_V3_actual.json), calibración de ocupación (`Datos/Preparados/V3/Calibracion_ocupacion_20261107/README.md`, archivo del entorno local; fuera de esta distribución) e [índice histórico](../../Historico/README.md).
