> **Prueba histórica retirada / vista previa fuera del dataset.** El 23/10/2026 sus imágenes de revisión se trasladaron al archivo local `.resguardo/orden_registros_20261023/vistas_pruebas_retiradas/recortes_lider2_001_005_20261022/`. Los planes, coordenadas, verificaciones y reversiones permanecen aquí. Las cifras e instrucciones siguientes describen aquella prueba, no el estado vigente.

# Vista previa: recortes de las fotos 001-005

Copias locales del tramo central. No se reemplazaron imagenes ni anotaciones de CVAT.

Las cinco imagenes PNG conservan los pixeles del recorte original, una vez aplicada la orientacion EXIF; no se redimensionaron. Las vistas JPG son solo para revision.

## Archivos

- `comparacion_001_005.jpg`: originales con ventana de recorte arriba y resultados debajo.
- `recortes_001_005.jpg`: vista conjunta de las cinco copias.
- `recortes_001_005_anotaciones.jpg`: vista conjunta con las 15 anotaciones manuales existentes trasladadas.
- `lider_2_00N_recorte.png`: copia recortada a resolucion completa.
- `anotaciones_recortadas_vista_previa.json`: coordenadas trasladadas; no es un archivo de importacion automatica.
- `manifest.json`: procedencia, coordenadas, dimensiones y verificacion de hashes y pixeles.

## Limites de esta prueba

La perspectiva deja pequenas franjas de modulos vecinos en los bordes. El recorte rectangular no garantiza eliminar todas las instancias laterales sin cortar el tramo central. Estos archivos no se incorporan al entrenamiento. El nivel superior sigue pendiente de anotacion, como en el trabajo 67; no se crearon nuevos poligonos. Se requiere revisar exhaustividad y visibilidad antes de preparar un dataset.

Original y copia deben conservar familia, escena y particion para evitar fuga entre conjuntos.

| Foto | Caja en original orientado (x0, y0, x1, y1) | Tamano | Poligonos conservados |
|---|---|---|---|
| 001 | [245, 180, 2880, 3780] | 2635 x 3600 | 3 |
| 002 | [345, 200, 2860, 3780] | 2515 x 3580 | 3 |
| 003 | [300, 160, 2820, 3740] | 2520 x 3580 | 3 |
| 004 | [200, 160, 2730, 3740] | 2530 x 3580 | 3 |
| 005 | [280, 300, 2715, 3790] | 2435 x 3490 | 3 |
