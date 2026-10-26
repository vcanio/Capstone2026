# Verificación local de Walmart Vision V3 · 25/10/2026

**Ampliación de ocupación del 26/10:** `spatial_signal_abstention_v2` conserva señal, métricas y máscaras; añade revisión por señal periférica ambigua. Se compararon 151 fotos de desarrollo y 754 detecciones, con 35 revisiones adicionales y cero transiciones nuevas a Reponer. No se integraron los filtros agresivos ni se calibró ocupación. Las pruebas de señal (20) y de aplicación V3 e interfaz (49) pasan. Informe y recibos HTTP de la entrega: `Documentacion/Desarrollo/Afinado_senal_ocupacion_V3_20261026.md` y `.resguardo/afinado_ocupacion_20261026/` en el proyecto fuente.

El paquete contiene únicamente el best.pt de `v3_afinado_papeles_huevos_20261026_011847_7021`. Su hash se comprueba al empaquetar, extraer y cargar la aplicación. La revisión V2 de las entregas anteriores no acredita V3.

En el equipo de desarrollo se comprobaron por HTTP: detección más bordes, Solo YOLO, recorte con alcance visible y Revisar, objeto con medición suspendida, y persona declarada con Góndola tapada y cero contornos. Se rechazaron confianza menor a 0,60 y visibilidad sin indicar. Se conservaron las máscaras V3 sin convertirlas en cuadriláteros. Las pruebas de la aplicación y laboratorio cubren además archivos modificados, límites de imagen, reinicio de resultados, vistas, estados y archivado reversible.

Evidencias operativas: `.resguardo/cierre_v3_20261025/` en el proyecto fuente. La integración reutiliza el estimador existente de bordes, color y textura: no lo presenta como calibrado para V3. La visibilidad es declarada por el usuario, no reconocida automáticamente.

No se ejecutó la reserva final de 63 fotos. No se certifican una instalación en otro computador, Mac físico, una nueva construcción Docker ni una sesión remota de Colab con estas comprobaciones locales. Se conservaron todos los pesos históricos y las dos incidencias de le_g10. El usuario autorizó cerrar e integrar la versión tras la revisión visual; las métricas históricas no se reescribieron.
