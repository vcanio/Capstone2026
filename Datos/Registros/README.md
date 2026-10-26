> **Alcance de este registro de procedencia.** La V3 vigente reúne **469 imágenes (337 train / 69 val / 63 test)**. Los inventarios, tareas y particiones descritos aquí conservan su versión y fecha; las menciones de un conjunto actual de 458 imágenes corresponden a la etapa anterior a las 11 tomas de refuerzo. Los lotes se solapan y no deben sumarse como datasets independientes. [Estado vigente y límites](../../Documentacion/Modelo_V3_actual.md).

# Registros V3 actuales

**Estado al 26 de octubre de 2026:** modelo V3 entrenado e integrado localmente. La app utiliza el best.pt del afinado de papeles, huevos y superiores vacíos. La nueva release sigue pendiente.

| Registro vigente | Resumen |
|---|---|
| Partición `v3_469_afinado_20261025` | 469 imágenes; 337 train / 69 val / 63 test. |
| Exportación de train | 336 imágenes utilizables; una permanece desactivada. |
| Selección `afinado_papeles_huevos_20261025` | 113 fotos: 67 reales y 46 sintéticas. |
| Validación del afinado | 22 reales y 47 sintéticas, separadas. |
| Reserva test | Las mismas 63 fotos; sin utilizar. |
| Ensayo vigente | `v3_afinado_papeles_huevos_20261026_011847_7021`, checkpoint best. |

[Resumen público verificable](../../Documentacion/Estado_V3_actual.json) · [Datos](../README.md) · [Modelo y límites](../../Documentacion/Modelo_V3_actual.md)

Los registros completos de trabajo se conservan en el entorno del equipo. La documentación pública no incluye fotografías privadas ni sustituye las anotaciones.

## Mantener la trazabilidad

- Conservar juntas las escenas relacionadas y sus variantes.
- Revisar las anotaciones antes de exportar o entrenar.
- No usar test para ajustar modelos, umbrales ni reglas de la app.
- Distinguir catálogo, fotos exportables y selección real de cada afinado.
- Conservar los registros fechados anteriores sin presentarlos como configuración vigente.

La configuración histórica `dataset_activo.json` pertenece a los primeros ensayos; no identifica este V3.
