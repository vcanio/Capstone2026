# Evolución de modelos y versión vigente

El modelo vigente es **V3-YOLO26**, best.pt de `v3_afinado_papeles_huevos_20261026_011847_7021`, integrado por decisión de Vicente. [Identidad, métricas y límites](../Modelo_V3_actual.md).

| Etapa | Cambio |
|---|---|
| V1 | Cuatro estados visuales por nivel. [Registros YOLO11](../../Historico/Experimentos/YOLO11-1_20261015_013749_f709/) y [YOLO26](../../Historico/Experimentos/YOLO26-1_20261015_021212_c452/). |
| V2 | Dos estados: reponer y suficiente. [Registros YOLO11](../../Historico/Experimentos/v2_base_yolo11n_01_20261020_002800_ec8d/) y [YOLO26](../../Historico/Experimentos/v2_base_yolo26n_01_20261020_004933_b105/). |
| V3 | Una clase geométrica Nivel; separar detección, señal de ocupación y decisión de revisión. |
| Afinado V3 vigente | Refuerzo de papeles, huevos y superiores vacíos, con repaso. Selección de 113 fotos; validación de 22 reales y 47 sintéticas. |

Las métricas entre etapas usan clases y particiones diferentes y no son una comparación directa. En la validación común del último afinado, mAP50–95 de máscaras bajó 90,49→88,96 % en reales y 86,01→85,33 % en sintéticas. La adopción fue una decisión del usuario tras revisión visual, no una mejora global demostrada.

Persisten las incidencias `le_g10`: superior de 029 sobredelimitado y superior de 030 omitido. Ocupación experimental 70/30 y umbral 30 %, sin calibración V3; visibilidad manual y abstención ante señal ambigua. Test 63 reservado.

Los checkpoints locales antiguos fueron retirados durante la limpieza autorizada anterior. La reorganización conserva todos los archivos que ya estaban en Git y todas las releases y activos existentes. Los registros numéricos publicados se consultan en Histórico y la ficha V3 conserva el estado del modelo actual.
