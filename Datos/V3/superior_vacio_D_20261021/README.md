# Casos D · nivel superior vacío

40 ediciones mediante la herramienta integrada de generación de imágenes. Se elimina toda la mercancía del primer nivel de venta completo, conservando el resto de la escena. Las zonas de reserva recortadas por encima de una franja azul permanecen. Se derivan solo de las 40 familias de entrenamiento y conservan su escena y partición; las reservas de validación y prueba no cambian.

[Abrir la tarea única en CVAT](https://pcvicen.tailca514b.ts.net/tasks/27) · [Comparar original y D](revision.html) · [Inventario de los 40 D](inventario.csv) · [Procedencia y hashes](manifest.json).

La tarea contiene **276 imágenes: 59 originales + 177 A/B/C + 40 D**, ordenadas por foto y variante. Trabajos 64/65/66 de 92/95/89 imágenes, conservando familias completas y la ausencia de asignación de la tarea anterior. La tarea 23 y sus trabajos se retiraron después de verificar el reemplazo y el respaldo recuperable.

Se conservaron los 1.212 polígonos existentes y se añadieron **204 contornos borrador**, escalados desde los originales, todos con `delimitacion=pendiente`. Su relación con cada foto, puntos y atributos se verificó al importar. El escalado no aprueba su geometría: revisar el ajuste de cada contorno, especialmente el límite superior abierto y la foto 059 de dos módulos, antes de entrenar.

Las 40 ediciones tienen revisión visual del asistente; **la aprobación humana está pendiente**. Nueve fotos necesitaron retoques: 022, 029, 030, 031, 032, 043, 046, 047 y 055. La 046 tiene revisión 3 y las otras ocho revisión 2. Las superficies que estaban ocultas son reconstrucciones de IA y pueden diferir de la góndola real. No se certifica una coincidencia píxel a píxel fuera de la zona editada ni una mejora del modelo sin entrenamiento y evaluación.

En `imagenes/` hay únicamente las 40 versiones finales. `prompts/` conserva el prompt personalizado de cada foto y cada retoque; todos parten del [prompt base D](prompt_base_D.txt). `registros/` documenta generación y revisión. Las versiones descartadas, planes de trabajo y respaldo completo de CVAT se conservan fuera del lote, en `.resguardo/casos_D_V3_20261021`.

[Guía de la tarea](guia_cvat.md) · [Criterio general V3](../../../Documentacion/Desarrollo/Criterio_V3_niveles.md) · [Registro de carga verificada](../../Registros/CVAT/tarea_27.json).

El entrenamiento sigue deshabilitado. El 22 de octubre se aplicó en toda la tarea 27 la [regla de mediana para niveles superiores sin tope claro](../../../Documentacion/Desarrollo/Regla_nivel_superior_mediana_V3.md): 168 superiores ajustados, 108 con cubierta clara conservados y 1.140 contornos inferiores intactos. La revisión humana de los contornos y la evaluación con fotografías reales de escenas independientes siguen pendientes.
