# Tarea 27: apoyo del superior sobre el portaprecio

Corrección general solicitada por el usuario el 22 de octubre de 2026 tras aprobar el ejemplo `lider_express_046_B_baja.png`. [Abrir tarea 27](https://pcvicen.tailca514b.ts.net/tasks/27).

La base del área útil se coloca **en la superficie de apoyo, por encima del portaprecio**, y desde ahí se proyecta la mediana de las alturas de los inferiores cuando no hay un tope físico claro. El borde superior del polígono de abajo no se reutiliza automáticamente: puede representar la cara inferior del estante. La franja del portaprecio queda fuera.

Se revisaron visualmente las 59 originales y las 217 variantes, incluyendo casos vacíos. Los candidatos geométricos se contrastaron con cada imagen y se corrigieron cuando seguían una baranda, un reflejo o un cartel. No se aplicó un grosor fijo a todo el lote.

| Resultado | Cantidad |
|---|---:|
| Imágenes revisadas | 276 |
| Superiores corregidos | 161 |
| Originales corregidas | 33 |
| Variantes corregidas | 128 |
| Superiores conservados | 115 |
| Con tope físico conservado | 108 |
| Abiertos con apoyo ya correcto | 7 |
| Inferiores conservados exactamente | 1.140 |
| Polígonos totales, mismos IDs | 1.416 |

La familia 010 (frames 41–44, trabajo 64) requiere una excepción: tras corregir la base, ambos extremos del límite superior calculado quedan fuera del encuadre. Se recortan los cuatro polígonos existentes a y=0 y se cambia únicamente su atributo `delimitacion` a `parcial`. El registro conserva la mediana y las coordenadas completas antes del recorte. No se añaden niveles, tags ni tracks.

Los cuatro niveles inferiores de 046 B y su superior previamente aprobado permanecen intactos. Se conserva la geometría de todos los inferiores del lote. Los demás atributos se mantienen. La operación no aprueba los datos para entrenamiento ni modifica las otras tareas.

## Evidencias

- [Plan completo por imagen](plan.json): apoyo, referencias, medianas, coordenadas y recortes.
- [Verificación posterior de CVAT](verificacion.json): igualdad exacta con el plan y conservación del resto.
- Láminas de revisión: rojo indica la base anterior; verde, la corregida. [1](revision_01.jpg), [2](revision_02.jpg), [3](revision_03.jpg), [4](revision_04.jpg), [5](revision_05.jpg), [6](revision_06.jpg), [7](revision_07.jpg), [8](revision_08.jpg), [9](revision_09.jpg), [10](revision_10.jpg), [11](revision_11.jpg).

Respaldo privado de las anotaciones y guías anteriores, solicitudes y lecturas posteriores: `.resguardo/apoyos_t27_20261022`. Instrucciones permanentes: `AGENTS.md`, la guía V3 y la regla de mediana; las guías de CVAT 10 y 11 incorporan el mismo criterio.
