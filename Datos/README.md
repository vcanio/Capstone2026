# Datos del modelo actual

Walmart Visión V3 utiliza una sola clase, **Nivel**, para delimitar el área útil de las repisas.

## Catálogo y partición

El catálogo vigente contiene **469 imágenes: 192 reales y 277 sintéticas**.

| Partición | Imágenes en catálogo | Uso |
|---|---:|---|
| Train | 337 | Aprendizaje; una imagen desactivada, 336 exportables. |
| Val | 69 | Selección y revisión: 22 reales y 47 sintéticas separadas. |
| Test | 63 | Reserva final sin utilizar. |

Las vistas de una misma escena y sus variantes se mantienen juntas para reducir la fuga de información. La partición activa se identifica como `v3_469_afinado_20261025`.

## Último afinado

El modelo actual aprendió con una selección de **113 fotos**, no con todo el catálogo: **67 reales y 46 sintéticas**.

Incluye 32 superiores vacíos, 11 tomas reales nuevas, seis fotos de huevos y 64 de repaso. El repaso cubre las 26 escenas del entrenamiento anterior. Las fotos sintéticas son variantes de fuentes existentes, no capturas independientes.

Las anotaciones se revisan por personas. Las marcas de oclusión y delimitación no convierten el modelo en un detector automático de visibilidad.

[Resumen V3](V3/README.md) · [Registros actuales](Registros/README.md) · [Ficha del modelo](../Documentacion/Modelo_V3_actual.md)

## Procedencia y conservación

Las carpetas conservan la ubicación original de sus fuentes. Que una foto esté físicamente en una carpeta de una etapa anterior no significa que sea otro dataset que deba sumarse a V3.

Las fotografías privadas y los pesos se distribuyen por separado; actualizar esta documentación no los publica. Los inventarios y ensayos anteriores se conservan como trazabilidad y se consultan desde el [archivo documental](../Historico/Documentacion/README.md).
