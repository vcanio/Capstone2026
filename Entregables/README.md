# Distribución de Walmart Visión

## V3 · release preparada como borrador

Se prepara **Walmart Visión V3 · niveles y ocupación experimental**, tag previsto `walmart-vision-v3-2026-10-26`. El borrador reúne:

- `Walmart_Vision_V3_20261026.zip`: app Windows x64, alternativa Docker y único best.pt V3 vigente.
- `Walmart_Vision_V3_20261026.sha256`: comprobante de integridad del ZIP.

**El borrador todavía no es una descarga pública.** Las [Releases publicadas](https://github.com/vcanio/Capstone2026/releases) conservan sus versiones anteriores. No se reemplazan sus activos.

V3 usa una sola clase Nivel, confianza fija 0,60 y ocupación experimental por bordes, color y textura. Requiere fotos frontales o casi frontales y confirmación manual de visibilidad. Incluye la abstención por señal superior o periférica ambigua; no detecta automáticamente personas, carteles o vacío.

El archivo automático Source code contiene fuentes, sin el modelo operativo incluido en el ZIP de la aplicación. La primera preparación requiere conexión; la inferencia posterior es local. El procedimiento Docker fue probado correctamente por Vicente en macOS con la release anterior; V3 conserva ese flujo y sus dependencias.

[Manual](../Documentacion/Usar_Walmart_Vision.md) · [Criterios y cálculo](../Documentacion/Guia_para_entender_el_proyecto.md) · [Modelo y métricas](../Documentacion/Modelo_V3_actual.md)

## Material académico

El [informe intermedio](../Documentacion/Informe_Intermedio_Avance_20261020.md) y su [PDF](Informe_Intermedio_Avance_20261020.pdf) conservan sus resultados fechados. Son antecedentes académicos; no certifican el comportamiento de la V3 actual.
