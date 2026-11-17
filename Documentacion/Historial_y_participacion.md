# Historial y participación del equipo

Lectura del historial público al 16/11/2026. Se conservan commits, autores y entregas de Fase 1/Fase 2; no se reescribe el historial para aparentar una distribución diferente del trabajo. Los ejemplos siguientes son verificables en GitHub y no constituyen un reparto exhaustivo de responsabilidades.

## Participación registrada

| Integrante y autor visible en Git | Evidencia concreta | Qué acredita |
|---|---|---|
| **Vicente Canio** (`Vicente`, `Vicente Canio`, `vcanio`) | [Cierre MVP `d96a9b5`](https://github.com/vcanio/Capstone2026/commit/d96a9b5), [documentación Línea A `91549a9`](https://github.com/vcanio/Capstone2026/commit/91549a9), [corrección de lectura `6243467`](https://github.com/vcanio/Capstone2026/commit/6243467) | Integración de apps, scripts, persistencia/reportes, documentación técnica y mantenimiento del MVP. |
| **Paulo Guerra** (`PauloG361`) | [Bordes `ee9650e`](https://github.com/vcanio/Capstone2026/commit/ee9650e), [combinación ponderada `8d2b072`](https://github.com/vcanio/Capstone2026/commit/8d2b072), [evidencias Fase 1 `0b976f0`](https://github.com/vcanio/Capstone2026/commit/0b976f0) | Modificaciones al procesamiento clásico de bordes, incorporación de ponderación entre ancho y altura y entrega de documentos individuales. |
| **Vicente Vilches** (`vivilchesm-rgb`) | [Evidencias Fase 1 `e94acdf`](https://github.com/vcanio/Capstone2026/commit/e94acdf), [informe Fase 2 `3d4621e`](https://github.com/vcanio/Capstone2026/commit/3d4621e) | Incorporación de entregables académicos de las dos fases. Estos commits no bastan para atribuir autoría de módulos de código adicionales. |

Un commit identifica al autor declarado y el cambio registrado. La captura, anotación, revisión visual y discusión conjunta también forman parte del desarrollo, pero no se cuantifican por número de commits. Los alias de una persona pueden aparecer separados en las estadísticas. No se atribuyen a otros integrantes cambios subidos desde una sola cuenta sin evidencia adicional.

## Hitos consultables

| Hito | Referencia |
|---|---|
| Entregas académicas de septiembre/octubre | [Historial completo](https://github.com/vcanio/Capstone2026/commits/main/), [Fase 1](../Fase%201/) y [Fase 2](../Fase%202/). |
| Revisión documental del oficial, 11/11 | [`2467a62`](https://github.com/vcanio/Capstone2026/commit/2467a62974c3f5b28b0e4548bd4c0527230cc8cd). |
| Simplificación pública centrada en las apps | [`3d13457`](https://github.com/vcanio/Capstone2026/commit/3d13457d84f4310f998e76f1592dcffb3886ac96); antecedentes accesibles en [Archivo del desarrollo](Archivo_del_desarrollo.md). |
| Línea A v2.2, 16/11 | [`bd22e4e`](https://github.com/vcanio/Capstone2026/commit/bd22e4e); reevaluación sobre imágenes ya observadas, sin nuevo entrenamiento del localizador. |
| Cierre MVP, 16/11 | [`d96a9b5`](https://github.com/vcanio/Capstone2026/commit/d96a9b5), [release](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-mvp-2026-11-16) y [CI](https://github.com/vcanio/Capstone2026/actions/workflows/comprobar.yml). |

## Consultar el historial desde un clon

```bash
git log --date=short --format="%h %ad %an %s"
git shortlog -sne HEAD
git show --stat ee9650e
git show --stat 3d4621e
git log --follow -- Aplicacion/ocupacion_linea_a.py
```

`shortlog` cuenta commits por identidad declarada; no equivale a horas, responsabilidad ni porcentaje de participación. `--follow` sigue cambios de ruta de un archivo cuando Git puede inferirlos. La [planificación](Planificacion_y_metodologia.md) y la [metodología](Metodologia_desarrollo_y_revision.md) complementan esta evidencia con el proceso de trabajo.

[Volver al README](../README.md)
