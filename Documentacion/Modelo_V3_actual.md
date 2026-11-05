# Modelo actual de Walmart Visión

**V3 oficial · refuerzo de geometría**, adoptado por Vicente el 5 de noviembre de 2026. [Descargar app y modelo](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.zip) · [Release](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05).

| Campo | Valor |
|---|---|
| Arquitectura | YOLO26n-seg |
| Clase | `Nivel` |
| Checkpoint | `best.pt` |
| Ensayo | `v3_refuerzo_geometria_revision_20261105_022414_e6f0` |
| SHA-256 | `7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a` |
| Afinado | 171 imágenes, 40 épocas, AdamW, lr 0,0001, batch 2, resolución 640, semilla 42 |
| Selección del best | Fitness combinado de cajas y máscaras; máximo del CSV en época 35 |
| Confianza en la app | Inicial 0,60; ajustable desde 0,25 |

| Máscaras | Fotos | mAP50 | mAP50–95 |
|---|---:|---:|---:|
| Validación real | 59 | 99,50 % | 89,95 % |
| Diagnóstico sintético | 34 | 99,50 % | 93,14 % |

La partición de desarrollo es `v3_refuerzo_geometria_20261104`, con selección `revision_geometria_20261104`. Las escenas relacionadas se agruparon antes del ensayo. Los valores no son comparables directamente con los agregados históricos de otra partición. No se evaluó ocupación y la reserva final de 63 fotos permanece sin utilizar.

El modelo localiza áreas de niveles; no decide directamente reposición ni detecta personas u obstáculos. La app conserva las máscaras y estima cobertura del frente mediante bordes, color y textura, con umbral experimental 30 %. Requiere revisión humana y no mide stock oculto. La mediana es un criterio de anotación y no se fuerza durante la inferencia.

Pueden existir omisiones y contornos incorrectos. Las incidencias históricas de superiores no se declaran resueltas por esta adopción. Las pruebas de funcionamiento no constituyen una calibración de ocupación ni una evaluación exhaustiva de precisión. [Registro de adopción](Desarrollo/Modelo_oficial_V3_20261105.md) · [Resumen estructurado](Estado_V3_actual.json).
