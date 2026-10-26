# Modelo vigente y resultados

La aplicación local utiliza únicamente el **best.pt del afinado V3** `v3_afinado_papeles_huevos_20261026_011847_7021`.

| Dato del último afinado | Resultado |
|---|---|
| Clase | Nivel |
| Fotos para aprender | 113: 67 reales y 46 sintéticas |
| Épocas completadas | 29 |
| Mejor checkpoint elegido | Época 19 por fitness combinado |
| mAP50–95 de máscaras, 22 reales | 88,96 % |
| mAP50–95 de máscaras, 47 sintéticas | 85,33 % |
| Test final | Reservado, sin utilizar |

Estas cifras miden segmentación, no ocupación ni reposición. La validación común bajó respecto del padre; la adopción fue una decisión tras revisión visual, con limitaciones conocidas.

[Ficha completa del modelo](../Documentacion/Modelo_V3_actual.md) · [Resumen numérico](../Documentacion/Estado_V3_actual.json)

## Trazabilidad

Cada ensayo conserva sus configuraciones, métricas y referencias de datos. Las etapas anteriores se consultan en el [archivo de ensayos](../Documentacion/Historico/Ensayos_V1_V2_20261020.md); no son alternativas ofrecidas por la app V3.

Las imágenes privadas, resultados extensos y pesos del laboratorio no se publican mediante esta actualización documental.
