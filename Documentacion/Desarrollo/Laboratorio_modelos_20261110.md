# Laboratorio de modelos simplificado · 10 de noviembre de 2026

El flujo operativo se centra en preparar datos o etiquetas, entrenar y revisar resultados. Se retiraron de la navegación la prueba individual de fotos, sus accesos desde resultados y la galería de reserva final. El enlace permanente «Abrir app de revisión» abre la app del equipo en el puerto 8095; no cambia automáticamente el modelo de esa app.

## Interfaz

- Inicio con dos recorridos: segmentación de niveles y clasificación de visibilidad.
- Tres pasos consistentes en ambos recorridos, sin el segundo listado redundante de cinco etapas.
- Estado de conexión explícito y recuperación ante errores.
- Métricas geométricas visibles, curva y valores por época bajo demanda.
- El modelo oficial muestra su aceptación y conserva su decisión cerrada. Otros ensayos mantienen el formulario manual y sus borradores durante las actualizaciones del catálogo.
- Etiquetado del clasificador identificado como preparación de etiquetas en CVAT.
- Revisión de composición en escritorio (1280 × 720) y móvil (390 × 844), en temas claro y oscuro. Se restauró el tema oscuro inicial y se retiró el tamaño de prueba del navegador.

## Compatibilidad y alcance

Los controles históricos V1/V2 permanecen ocultos e inertes fuera de la navegación para mantener la compatibilidad del controlador existente. Sus APIs, módulos y registros se conservan. Los módulos de predicción V3 y de galería final ya no se cargan desde la interfaz. Un acceso antiguo a la vista de predicción lleva a resultados.

No se modificaron aplicaciones de revisión, pesos, particiones, anotaciones, registros congelados, releases ni clones de publicación. No se inició entrenamiento, inferencia ni preparación de datos, y no se abrió CVAT. Se consultaron metadatos del catálogo y del modelo oficial; las imágenes usadas en el escenario de seguimiento fueron SVG sintéticos del servidor aislado.

## Comprobaciones

- 78 pruebas de interfaz, continuidad de IDs, decisiones, entrenamiento, catálogo operativo, preferencias, sondeo y sincronización: correctas. Salida: pruebas.txt (`Documentacion/Desarrollo/Verificaciones/laboratorio_20261110/pruebas.txt`, archivo del entorno local; fuera de esta distribución).
- Sintaxis de los tres módulos JavaScript modificados: correcta.
- Sintaxis Python y construcción de 24 escenarios sintéticos: correctas.
- Navegador: recorridos de segmentación y clasificación, resultados del modelo oficial, configuración del refuerzo, ausencia de navegación a predicción y estados vacío, error y entrenamiento simulado. El formulario de entrenamiento permaneció bloqueado durante el trabajo simulado; no se pulsó ningún inicio de trabajo.
- Hash del best.pt oficial: coincide con `7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a`. Recibo: modelo_oficial.json (`Documentacion/Desarrollo/Verificaciones/laboratorio_20261110/modelo_oficial.json`, archivo del entorno local; fuera de esta distribución).
- Detector visual Impeccable ejecutado una vez: avisos sobre imágenes con fuente asignada dinámicamente, elementos históricos ocultos, gráficos con borde superior y animación histórica de importación. No se observaron imágenes rotas ni errores de JavaScript en el recorrido final.

La interfaz se sirve mediante el montaje de código ya existente del contenedor local: basta recargar el laboratorio. No se reinició el servicio ni se publicaron cambios en GitHub.
