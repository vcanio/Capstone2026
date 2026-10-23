# Mapa del proyecto

Estado local del **23 de octubre de 2026**. El laboratorio y la aplicación tienen versiones distintas: la aplicación utiliza dos modelos V2 ya entrenados; el trabajo de datos actual prepara V3 con una sola clase geométrica `Nivel`. V3 todavía no tiene un entrenamiento aprobado.

## Dónde empezar

| Necesidad | Entrada |
|---|---|
| Usar la aplicación con una foto | [Entregables](../../Entregables/README.md) y [manual de usuario](../Usar_Walmart_Vision.md) |
| Continuar las 458 imágenes V3 | [Registros de datos](../../Datos/Registros/README.md) |
| Revisar anotaciones y correcciones | [CVAT y sus tareas](../../Datos/Registros/CVAT/README.md) |
| Ver entrenamiento, métricas y pesos anteriores | [Experimentos](../../Experimentos/README.md) |
| Ubicar programas y verificadores | [Herramientas](../../Herramientas/README.md) |
| Preparar Docker o el laboratorio | [Infraestructura](../../Infraestructura/README.md) |
| Revisar informe, metodología y antecedentes | [Documentación](../README.md) |

## Responsabilidad de cada carpeta

| Carpeta | Contenido | Regla de conservación |
|---|---|---|
| `Datos/` | Fotos, variantes y registros de procedencia, tareas y particiones. | Inventario y hashes; escenas y variantes juntas. |
| `Herramientas/` | Código, iniciadores y pruebas. `Demo_lite/` conserva el nombre técnico del visor. | Los resultados van en datos, experimentos o evidencias, no junto al código. |
| `Experimentos/` | Ensayos, pesos entrenados, métricas y pruebas de algoritmos. | No sobrescribir resultados de un ensayo. Las pruebas del panel no entran al entrenamiento. |
| `Modelos/` | Pesos generales preentrenados y procedencia. | Los pesos entrenados propios están en cada ensayo. |
| `Entregables/` | ZIP listo para usar, hashes, cuaderno y copias del informe. | Fechas y contenido explícitos; conservar bytes de entregas anteriores. |
| `Documentacion/` | Guías, informe, ejemplos y evidencias resumidas. | Lo vigente se distingue de los documentos históricos fechados. |
| `Infraestructura/` | Configuración de servicios, Docker y CVAT. | Los accesos personales y `.env` reales son locales. |
| `reproducibilidad/` | Manifiestos de activos y verificaciones de entregas fechadas. | No presentar un manifiesto anterior como si incluyera todos los cambios nuevos. |

## Carpetas locales de trabajo

- `.publicacion/` conserva el checkout Git con cambios locales, los paquetes del laboratorio y registros de distribución. Su índice local `.publicacion/README.md` explica cada grupo. Es distinto de la raíz del laboratorio, que no tiene `.git`.
- `.resguardo/` guarda respaldos y el material retirado, con recibos de traslado. No es otro dataset activo.
- `.tmp/` se reserva a entradas de generación o instancias locales aún necesarias. Su índice identifica lo conservado y los temporales archivados.
- `.venv-modelo/` y `.venv-cvat/` son entornos instalados. No se eliminan como si fueran cachés sueltas.
- `Contexto/` contiene material privado de referencia. Se conserva fuera de la publicación.

El material académico `Fase 1/` se conserva en el checkout de publicación; no se copia a esta raíz para simular que es otro insumo de entrenamiento.

## Estado de los datos

Los seis lotes registran **567 imágenes únicas** de todas las etapas. V3 reutiliza parte de ellas y reúne **458**, con 181 reales y 277 sintéticas. Su reparto fijado es **327 entrenamiento / 68 validación / 63 prueba**, en 43 grupos conservadores. [Estado y fuentes](../../Datos/Registros/estado_actual.json).

Los cuatro ensayos V1/V2 siguen siendo antecedentes válidos. El ZIP actual incluye únicamente los dos modelos V2. Una nueva limpieza, guía o partición no aprueba anotaciones, no reentrena modelos y no recalibra la ocupación.

## Mantener este orden

1. Actualizar el índice correspondiente al incorporar un lote, ensayo, entrega o herramienta.
2. Guardar una evidencia pequeña y fechada de las verificaciones. Los logs y renders completos se archivan en local.
3. Antes de eliminar, distinguir fuentes, resultados irrepetibles y archivos regenerables. Conservar los primeros y documentar los traslados.
4. Ejecutar `Herramientas/verificar_proyecto.py` antes de cerrar cambios de estructura. Los hashes de datos y las referencias de los ensayos deben conservarse.

[Volver al README principal](../../README.md).
