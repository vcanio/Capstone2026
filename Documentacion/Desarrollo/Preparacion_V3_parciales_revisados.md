# V3: regiones visibles parciales en la preparación

Decisión autorizada por el usuario el 25 de octubre de 2026: admitir regiones visibles parciales bien delimitadas y revisadas para entrenar el localizador de la clase `Nivel`.

## Avisos y bloqueos

`delimitacion=parcial` y `Occluded` generan avisos visibles con el ID del polígono. Pueden exportarse tras confirmar visualmente la región anotada y los límites recuperables. Un contorno incierto debe permanecer pendiente o llevar una marca de revisión de foto en CVAT.

Siguen excluidas las fotos con pendientes, delimitación desconocida, geometría inválida o incompatible, tracks, intervalos, marcas de revisión, ausencia de niveles o desactivación en CVAT. No se elimina un polígono problemático para exportar el resto de su foto.

## Exportación

La política `niveles_visibles_revisados_v3_20261025` se registra en las nuevas copias. Cada exportación requiere identificar al revisor y confirmar las regiones anotadas, incluidos parciales y ocluidos. Las copias anteriores y sus exportaciones permanecen intactas; se debe traer una nueva copia para aplicar el nuevo criterio.

El manifiesto conserva por imagen los avisos y, por nivel, ID, `delimitacion` y `Occluded`. Las etiquetas YOLO contienen solo la clase `Nivel` y las coordenadas normalizadas. No se cambia ningún dibujo ni atributo de CVAT.

Las 458 asignaciones por familia y escena se conservan. El test permanece fuera de `desarrollo.yaml`; validación real y sintética siguen separadas. La preparación no aprueba ni inicia entrenamiento V3.

## Ocupación

La ocupación visible V3 sigue pendiente de implementación. La política prevista muestra porcentaje de la región visible y aviso de recorte, sin extrapolar al nivel completo. El contenido oculto por una oclusión se trata separadamente.

## Comprobación inicial

La copia `v3_20261025_032846_3bcafc2f` contiene las 458 fotos y 2.314 polígonos: 457 fotos sin bloqueos técnicos (326 entrenamiento, 68 validación y 63 prueba). Los 37 niveles parciales y 202 ocluidos generan avisos en 107 fotos. Solo se excluye la foto desactivada `lider_express_043_D_superior_vacio.png`, con cuatro pendientes. Esta copia espera la revisión humana de exportación.

Se verificó que las anotaciones, los metadatos de CVAT y la partición no cambiaron respecto de la consulta anterior. Pasaron 18 pruebas de preparación/exportación, la sintaxis JavaScript y los verificadores de proyecto y partición. El respaldo y la comprobación están en `.resguardo/parciales_preparacion_v3_20261025/`.

[Volver al criterio V3](Criterio_V3_niveles.md) · [Preparación desde el panel](../../Laboratorio/Modelos/README.md)
