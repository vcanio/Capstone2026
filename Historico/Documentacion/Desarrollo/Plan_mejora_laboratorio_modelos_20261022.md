> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Plan de mejora del Laboratorio de modelos

Fecha: 22 de octubre de 2026. Estado: implementadas las mejoras de orientación, continuidad y revisión; V3 visible en preparación, con entrenamiento bloqueado hasta integrar sus dependencias. [Registro de implementación y verificación](Implementacion_laboratorio_modelos_20261022.md).

Prioridad indicada por Vicente: **saber qué sigue y qué está listo**.

## Objetivo

Al entrar, poder identificar el contexto de trabajo, lo que está terminado, lo pendiente y una acción siguiente con su motivo. Conservar el acceso directo a preparar datos, entrenar, comparar y probar fotos: el trabajo es iterativo y puede haber modelos utilizables mientras se prepara otra copia.

## Evidencia de la revisión

Se recorrieron en el panel local las pantallas de selección de versión, preparación, entrenamiento, resultados y pruebas de fotos. Se revisaron su HTML y lógica, el README del laboratorio y el criterio V3. La inspección visual fue en escritorio, tema oscuro; móvil, tema claro y estados de fallo quedan como validación de implementación.

1. El inicio muestra dos modelos disponibles en V2, pero la acción principal es siempre «Continuar a Preparar datos».
2. Una copia ya revisada sigue mostrando nombre de revisor, casilla y botón de aprobación; el texto dice que se puede entrenar, pero el formulario mantiene apariencia de tarea pendiente.
3. La navegación enumera secciones, sin mostrar cuáles están listas, bloqueadas o en ejecución para el contexto seleccionado.
4. En el recorrido, Resultados tenía YOLO26 seleccionado y Probar una foto tenía YOLO11. Las selecciones independientes no aseguran continuidad cuando se quiere probar el ensayo recién revisado.
5. El resumen de desarrollo usa 40 fotos, mientras las comparaciones guardadas por foto corresponden a la validación del entrenamiento. La explicación existe, pero exige leer texto secundario para advertir el cambio de conjunto.
6. Los nombres extensos de tareas y copias se cortan dentro de selectores. Se repite información de versión y criterio que puede ir en una ficha de contexto.
7. La interfaz ofrece V1 y V2; el criterio de V3 requiere una clase geométrica y validación separada de ocupación. No basta con agregar una tarjeta para habilitar ese flujo.

## Entrega 1 · Orientación y siguiente acción

### Inicio con resumen de trabajo

Mantener el selector de versión, pero al volver mostrar un resumen del contexto recordado y actualizado: criterio, lote, copia seleccionada, último ensayo relevante y acción recomendada. La versión se puede cambiar desde la cabecera.

Mostrar estados por objeto, evitando un único «todo listo» para la versión:

- Datos: sin importar, pendientes de revisión, requieren corrección o aprobados.
- Ensayo: sin iniciar, preparando, entrenando, evaluando, terminado, interrumpido o fallido.
- Evaluación: pendiente, disponible o no comparable con el ensayo elegido.
- Ocupación y alertas: estado independiente cuando el criterio lo requiera.

| Situación comprobada | Mensaje | Acción principal |
|---|---|---|
| No hay copia compatible | Faltan anotaciones para este criterio | Traer anotaciones |
| Copia importada con problemas | Esta copia tiene incidencias por resolver | Revisar incidencias |
| Copia técnicamente válida sin revisión humana | Falta registrar la revisión de esta copia | Revisar y aprobar |
| Copia aprobada sin ensayo asociado | Datos listos para crear un ensayo | Configurar entrenamiento |
| Ensayo en ejecución | El ensayo sigue en curso | Ver seguimiento |
| Ensayo fallido o interrumpido | El ensayo no terminó; indicar etapa y causa conocida | Revisar y recuperar |
| Modelo disponible sin evaluación requerida | Falta evaluar este modelo | Preparar evaluación, o explicar el requisito si aún no existe esa operación |
| Evaluación disponible | Resultados listos para revisar | Revisar resultados |
| Consulta fallida o desactualizada | No se pudo verificar el estado actual | Reintentar consulta |

Reglas: la recomendación indica a qué copia o ensayo se refiere; una copia nueva no invalida automáticamente un modelo histórico; no se elige «el mejor» por ser el más reciente; ninguna recomendación inicia entrenamientos o importaciones automáticamente. Mostrar alternativas discretas cuando convivan revisar una copia nueva y probar un modelo existente.

### Navegación con estado

Añadir texto breve e icono junto a cada sección: «Datos · aprobados», «Entrenamiento · en curso» o «Resultados · disponibles». El estado se calcula para el contexto activo. Usar color como apoyo, siempre acompañado de texto. Una acción bloqueada explica el motivo y ofrece acceso a resolverlo.

### Copia aprobada como tarea terminada

Reemplazar el formulario pendiente por un comprobante de revisión: copia, persona, fecha y alcance, con «Configurar entrenamiento con esta copia». El historial queda accesible. Una importación posterior conserva su propia revisión y estado.

Aceptación: desde el inicio se alcanza la siguiente tarea en una acción de navegación; una copia aprobada no parece pendiente; tras recargar se conserva el contexto válido y se consulta su estado actual.

## Entrega 2 · Continuidad y revisión accionable

### Contexto visible y nombres comprensibles

Cabecera compacta: «V2 base / Líder Express / copia del 19 oct / YOLO26». Separar criterio del proyecto, copia de anotaciones, ensayo y pesos. Usar nombres breves en selectores y mostrar nombre completo, identificador y procedencia en el detalle.

Acciones explícitas transportan el contexto: «Entrenar con esta copia», «Ver resultados de este ensayo» y «Probar este modelo». La navegación libre puede conservar las preferencias de cada pantalla, pero nunca debe cambiar silenciosamente el objeto de una acción contextual. Si el objeto ya no está disponible, explicar la causa.

### Preparación como revisión de pendientes

Encabezar la página con resumen de fotos, revisión y bloqueos. Ordenar incidencias por impacto y permitir abrir la foto o tarea de CVAT cuando exista una correspondencia comprobada. Separar errores que bloquean, advertencias y limitaciones de evaluación. Mantener visible la última consulta de CVAT: no afirmar que la copia está sincronizada sin comprobarlo.

### Entrenamiento con propósito

Añadir una nota opcional «Qué queremos comprobar» y un resumen previo del criterio, copia aprobada, partición, modelo de partida y cambios respecto del ensayo de referencia. Durante la ejecución, destacar el seguimiento; al terminar, ofrecer sus resultados. Los registros técnicos permanecen secundarios. El formulario para otro ensayo continúa disponible.

### Resultados que llevan a una decisión

Conservar el resumen de omisiones y falsas alertas ya existente. Añadir accesos a los casos que sustentan cada cifra cuando haya datos por foto. Si falta ese detalle, mostrar la limitación sin inventar filtros ni asociaciones.

Identificar cada bloque con su conjunto: validación original, originales reales de desarrollo, variantes sintéticas o reserva final. No presentar el conjunto mixto como evidencia exclusivamente real. Comparar cifras automáticamente solo con criterio, conjunto, referencias y parámetros de evaluación compatibles; explicar incompatibilidades.

Proponer un registro de decisión: candidato, seguir ajustando o descartado, con motivo y autor. «Entrenamiento terminado» no equivale a «modelo validado». No definir umbrales de aceptación nuevos como parte del cambio visual.

Aceptación: una acción «Probar este modelo» conserva el ensayo y pesos correctos; cada métrica identifica su conjunto; cada bloqueo ofrece una explicación útil; la reserva final permanece fuera de ajustes habituales.

## Entrega 3 · Incorporación explícita de V3

Mostrar V3 con su estado comprobado, inicialmente como preparación si no existe integración operativa. Dividir el avance en: anotaciones revisadas → datos exportables → localizador entrenado → localizador evaluado → ocupación validada → alertas validadas.

La integración funcional necesita esquema de una clase `Nivel`, exportador, validaciones, partición y evaluación compatibles. Es una entrega con dependencias de datos y servidor, además de interfaz. No habilitar entrenamiento por la mera presencia de una tarjeta V3.

En revisión, diferenciar delimitación completa, parcial y pendiente; oclusión y revisión de foto tienen significados propios. Un nivel no detectado, parcial o con contenido oculto no debe mostrarse automáticamente como 0 % de ocupación. Esos atributos manuales no se consideran predicciones del YOLO de una clase.

Conservar las reglas actuales: apoyo sobre portaprecio; superiores con criterio documentado; ninguna modificación automática de anotaciones manuales; no reintroducir el ensayo retirado de parciales de tarea 27 ni duplicar superiores ya registrados. El plan no supone que esos trabajos deban repetirse.

Aceptación: se puede reconocer qué parte de V3 está preparada y cuál falta; entrenar localización no marca ocupación o alertas como validadas; las acciones no implementadas explican su dependencia.

## Orden técnico y validación

1. Consolidar el cálculo de estado y recomendación en `static/lab-logic.js`, reutilizando `versionStatus`, `homeState` y validaciones existentes donde corresponda. Basarse en entidades identificadas y datos del servidor, sin duplicar una lógica de estados por pantalla.
2. Construir el resumen y las transiciones en `panel.html` y `static/panel.js`; guardar contexto estable en preferencias y revalidarlo al cargar. Ajustar jerarquía y densidad en `static/panel.css` conservando el diseño actual.
3. Incorporar solo los campos de servidor que falten para procedencia, evaluación y decisiones. No deducir estados de revisión o validación a partir de nombres de archivos.
4. Usar los escenarios del servidor de prueba de interfaz para comprobar falta de datos, revisión pendiente, copia aprobada, ejecución activa, fallo, resultados disponibles, comparación incompatible y V3 aún no habilitada.
5. Verificar especialmente el caso mixto: modelo anterior utilizable y copia nueva pendiente. Probar continuidad de identificadores entre pantallas y recuperación tras recargar.
6. Revisar escritorio y móvil, temas claro y oscuro, navegación con teclado, foco tras cambiar de pantalla, textos largos y explicación accesible de bloqueos.

Prueba de uso propuesta: abrir una versión y responder en menos de 10 segundos «qué está listo», «qué falta» y «qué debo hacer ahora». Esta es una meta de validación, no una mejora ya medida.

Primera implementación recomendada: **resumen inicial + siguiente acción + copia aprobada como tarea terminada + transiciones que conservan contexto**. Es el conjunto que atiende directamente la dificultad indicada por Vicente. Las estimaciones de tiempo deben hacerse después de confirmar los campos disponibles y el alcance de V3.

## Fuentes locales

- [Interfaz actual](../../../Laboratorio/Modelos/panel.html).
- [Lógica del laboratorio](../../../Laboratorio/Modelos/static/lab-logic.js).
- [Comportamiento y flujo vigente](../../../Laboratorio/Modelos/README.md).
- [Integración con CVAT](../../../Documentacion/Desarrollo/Integracion_CVAT_panel.md).
- [Criterio V3](../../../Documentacion/Desarrollo/Criterio_V3_niveles.md).
- [Regla de superiores V3](../../../Documentacion/Desarrollo/Regla_nivel_superior_mediana_V3.md).
