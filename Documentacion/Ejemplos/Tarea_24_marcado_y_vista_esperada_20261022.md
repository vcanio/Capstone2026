# Tarea 24: marcado V3 y resultado esperado en Walmart Visión

Propuesta visual solicitada por el usuario el 22 de octubre de 2026. Se consultó la tarea 24 de CVAT: 60 imágenes y 308 polígonos de clase Nivel. La demostración usa los frames 0, 1 y 2 (carro, cajas y persona), pertenecientes a entrenamiento. Son ediciones sintéticas. No se modificaron anotaciones ni código de la aplicación y no se ejecutó inferencia.

## Marcado propuesto

Un polígono por área útil completa del módulo. Se conserva la parte tapada únicamente si sus límites se pueden recuperar con respaldo geométrico fiable. La base queda sobre el portaprecio. La propuesta del superior abierto aplica la mediana de los cuatro inferiores: 191,13472499999995 px para los dos ejemplos de familia 001 y 200,98207499999998 px para familia 002. El cartel trasero no es techo. Estas propuestas no sustituyen los borradores pendientes de CVAT.

`delimitacion=completa` y `Occluded=true` son compatibles: el primero describe el perímetro recuperable y el segundo la presencia de un objeto delantero. Se activan N2, N4 y N5 en carro/cajas; N2 tiene además un cartel de precio colgante que invade el área del segundo nivel. En el ejemplo de persona se activan los cinco niveles.

Si el perímetro es incierto, corresponde parcial o Revision_foto; no inventar coordenadas para completar la figura. Consultar el [criterio V3](../Desarrollo/Criterio_V3_niveles.md).

## Vista esperada

Los niveles ocluidos se muestran como No evaluable, con ocupación sin medición y sugerencia de repetir la toma. Las compras del carro, las cajas y el producto sostenido por la persona no son stock del nivel. La parte tapada no se interpreta como vacío ni dispara una alerta automática de reposición.

Los niveles visibles quedan pendientes de medir: se usa un guion, sin porcentajes ilustrativos ni clasificación de reposición inventada. La demostración muestra el comportamiento propuesto de V3 y no una predicción del modelo actual. El atributo manual Occluded no será predicho automáticamente por el modelo de una clase; la inferencia requiere una comprobación de visibilidad propia y validada.

La interfaz de Walmart Visión utilizada para esta demostración ofrecía V1/V2 y cálculo experimental de ocupación. La entrega local actual incluye solo los dos modelos V2. Esta demostración conserva su lenguaje visual, pero no implementa V3 ni el control de oclusión en producción.

Fuente de revisión y propuesta local: `snapshot.json` y `propuesta.json`, originalmente en `.tmp/tarea24_demo_20261022/` y archivadas el 23/10 en `.resguardo/orden_proyecto_20261023/temporales_anteriores/tarea24_demo_20261022/`. La comparación interactiva preparada para este chat se guarda en su carpeta de visualizaciones del 22 de octubre.

**Actualización posterior:** el usuario pidió corregir la tarea 24. La [revisión aplicada y verificada](../../Datos/Registros/CVAT/revisiones/superiores_t24_20261022/README.md) ajustó 36 superiores por mediana y conservó 24 techos físicos, sin cambiar los inferiores ni las oclusiones. Esta demostración anterior conserva su carácter ilustrativo y no sustituye ese registro vigente.
