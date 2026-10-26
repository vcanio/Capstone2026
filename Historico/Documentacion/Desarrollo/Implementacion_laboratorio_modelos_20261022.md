> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Implementación del plan del Laboratorio de modelos

22 de octubre de 2026, hora de Santiago. Aplicación del [plan de mejora](Plan_mejora_laboratorio_modelos_20261022.md).

## Cambios disponibles

- El inicio muestra criterio, copia y ensayo seleccionados, estados separados de datos, ensayo, evaluación y ocupación/alertas, y una siguiente acción con su motivo. Las consultas fallidas muestran estado sin verificar y permiten reintentar. Volver al inicio reconsulta cuando el catálogo tiene más de 15 segundos.
- La navegación conserva el acceso a las secciones y añade iconos y texto de estado. Una copia nueva pendiente no invalida el modelo anterior: pueden coexistir revisar datos y probar un modelo histórico.
- Las copias aprobadas muestran un comprobante con identificador, persona, fecha y alcance. El formulario de aprobación deja de parecer pendiente. El botón de entrenamiento conserva exactamente la copia elegida.
- Las acciones contextuales transportan identificadores de copia, ensayo, pesos y, cuando existe correspondencia por nombre y SHA-256, fotografía. Si el objeto no está disponible se explica el problema. Las preferencias válidas se recuperan al recargar y se contrastan con el catálogo actual.
- Los nombres de las copias son breves; el detalle conserva nombres completos, IDs y procedencia. Preparación resume fotografías, bloqueos y advertencias, e identifica la fecha registrada de consulta de CVAT, sin afirmar sincronización en vivo.
- Entrenamiento permite registrar «Qué queremos comprobar», conserva un ensayo de referencia y muestra criterio, datos, partición, modelo de partida y cambios de configuración. El propósito queda en `config_interfaz.json`.
- Resultados permite probar los pesos de ese ensayo. Distingue explícitamente validación original y conjunto mixto de desarrollo. El detalle por foto muestra alertas omitidas, falsas alertas y omisiones de localización, sin confundir estas cifras.
- El registro de decisión admite candidato, seguir ajustando o descartado, con motivo y autor. El servidor guarda fecha e historial de forma atómica en `decision_modelo.json`, mediante `POST /api/runs/decision`. Guardar una decisión no acredita validación ni cambia métricas.
- Las diferencias automáticas exigen criterio, firma de fotos/referencias/partición y protocolo de evaluación compatibles. Los futuros ensayos guardan `protocolo_evaluacion.json` con parámetros explícitos que conservan los valores actuales de evaluación y la versión de Ultralytics. Los históricos sin ese registro permiten comparación visual con la limitación explicada; no se les inventó un protocolo ni se recalcularon sus métricas.

## Estado de V3

V3 aparece como preparación con seis avances separados: revisión de anotaciones, datos exportables, localizador entrenado, localizador evaluado, ocupación validada y alertas validadas. Faltan exportador, validaciones, partición y evaluación compatibles para habilitar el entrenamiento desde el panel. El servidor también rechaza entrenar una copia de una sola clase `Nivel` a través de la ruta actual.

La pantalla diferencia delimitación completa/parcial/pendiente, oclusión y revisión de foto. Explica que un YOLO de una clase no predice esos atributos y que un nivel parcial, oculto o no detectado no representa 0 % de ocupación. La implementación no ejecutó importaciones, entrenamientos ni modificaciones de anotaciones de CVAT; conserva las reglas y registros de superiores de las tareas 27 y 28.

## Verificación

- Suite completa: **250 pruebas, 0 fallos, 0 errores y 1 omitida**. La omitida es la integración real opcional de YOLO26, activable con `RUN_NIVELES_REAL=1`; no se entrenó para verificar esta interfaz. [Salida de la suite](../../../Documentacion/Desarrollo/Verificaciones/laboratorio_modelos_20261022/pruebas.txt).
- Tras los ajustes finales de textos y contexto, se repitieron las **55 pruebas** de flujo, estados, preferencias, sondeo e inventario: todas pasaron.
- En servidor sintético aislado se comprobaron copia pendiente, aprobada sin ensayo, resultados disponibles, ejecución activa, fallo, interrupción, errores de catálogo y actividad, comparación incompatible y V3 en preparación.
- Se verificó el caso mixto de copia nueva con incidencias y modelo histórico disponible; la selección explícita de los pesos y su conservación después de recargar; el comprobante de revisión; y guardar una decisión sintética. No se registró ninguna decisión sobre los modelos reales.
- Revisión visual en escritorio de 1440 × 1000 y móvil de 390 × 844, temas claro y oscuro, navegación por teclado y foco al cambiar de sección. El inicio móvil no presentó desbordamiento horizontal. Los nuevos textos extensos admiten salto de línea.
- En el panel real se comprobaron los **40 enlaces de casos**, con **10 originales reales y 30 variantes sintéticas**, asociados por nombre y hash. La reserva final permanece excluida. No se ejecutó inferencia al comprobar esos enlaces.
- El detector de diseño se ejecutó. Señaló componentes heredados: imágenes cuyo `src` se asigna al analizar, texto pequeño del seguimiento, bordes de énfasis y animación del indicador de importación. También señaló una combinación de contraste de 4,4:1 en su inspección automática. La inspección del nuevo resumen se realizó en ambos temas; no se declara una auditoría WCAG completa.

Se actualizaron pruebas antiguas del inventario que aún esperaban 170 imágenes y excluían las 30 variantes de diagnóstico, para verificar el comportamiento ya documentado de 200 imágenes en el catálogo base: 160 de aprendizaje y 40 de desarrollo. Las 36 imágenes de reserva final continúan excluidas. Esto no modifica la partición ni el conjunto exportado para entrenamiento.

El servicio local del panel se reinició después de comprobar inmediatamente que no había trabajos activos. Los contenedores y servidores sintéticos usados para la revisión se retiraron al finalizar. La meta de responder «qué está listo, qué falta y qué sigue» en menos de diez segundos queda como prueba de uso con el usuario; no se presenta como una mejora medida.
