# Almacenamiento local y alcance público

Las fotografías y los datasets completos no se distribuyen en GitHub. La app y su modelo operativo son autónomos y no requieren el disco de datos. El catálogo portable y los recibos detallados se conservan en el entorno local.

La raíz externa se configura con `WALMART_DATA_ROOT` o `.config-modelo/almacenamiento.local.json`. El laboratorio dispone de `almacenamiento_datos.py`, las herramientas de conexión/verificación y el override `Infraestructura/Docker/compose.modelos.datos.yml`, con montajes de lectura. Una copia pública del código no acredita la presencia de las fuentes necesarias para reproducir el entrenamiento.

Clasificación cerrada el 10/11: 519 fuentes distintas de train de la cadena oficial (299 reales/220 sintéticas) y 272 fuera de esa cadena, incluidas las 11 val actuales y las 68 revisadas de Ohiggins 3. Las 281 variantes de ocupación permanecen separadas. Las categorías no borran el historial de otros ensayos ni prueban independencia de escenas.

Las vistas clasificadas son enlaces duros: no editarlas para crear variantes. Las carpetas de imágenes externalizadas son junctions registradas: no borrarlas recursivamente. Fuentes compartidas, copias independientes, registros previos y metadatos congelados se conservan. Siete vistas antiguas ya faltaban al inicio; no se afirma una auditoría global aprobada.

[Modelo vigente](../../../Documentacion/Modelo_V3_actual.md) · [Guía de conexión](../../../Documentacion/Desarrollo/Datos_externos_20261108.md).
