# Criterio de oclusión por nivel

Decisión del 19 de octubre de 2026, por delegación del usuario. Se mantiene el esquema `Nivel` con `estado`: `reponer`, `suficiente` o `no_evaluable`, más la propiedad nativa `Occluded`.

## Regla de anotación

El objetivo es el espacio completo del nivel. Bajo oclusión parcial se conserva su contorno completo, incluida la parte oculta, cuando la geometría pueda establecerse de forma reproducible. Puede respaldarse en las repisas y límites visibles o, en estas ediciones sintéticas emparejadas, en el original orientado y escalado, comprobando que la edición conserva la estructura. No es obligatorio ver cada borde completo. Este es un criterio amodal: el polígono representa el nivel, no solo sus píxeles visibles.

Activar `Occluded` cuando una persona, carro u objeto tape parte de esa zona. Asignar el estado exclusivamente con la evidencia visible de la edición: `suficiente` si ya alcanza el 30 % del ancho completo, `reponer` si ni llenando lo oculto lo alcanzaría, y `no_evaluable` si lo oculto puede cambiar la decisión. La imagen original respalda la geometría; no determina el estado de stock de la edición.

Cuando no existe geometría reproducible ni una referencia verificada, registrar una incidencia y mantener el caso pendiente. No crear un contorno arbitrario ni aceptar la imagen como anotación terminada. Esta excepción no obliga a eliminar todos los casos con bordes ocultos.

## Decisión sobre los cuatro casos del lote 22

Conservar los niveles inferiores de la foto 001 con cajas, 028 con cajas, 050 con carro y 053 con cajas. Se compararon visualmente los contornos con los originales, aplicando la orientación EXIF y la escala a 1086 × 1448. Las repisas y los límites de la estructura coinciden en las zonas comprobables, y el original respalda la parte tapada. Las comparaciones están en `Datos/Registros/CVAT/revisiones/visibilidad_20261019T222744Z/decision_contornos/`.

El usuario autorizó aplicar el criterio para preparar la selección. Los cuatro polígonos quedaron conservados y sus incidencias técnicas se resolvieron, con el motivo registrado en CVAT. El quinto caso, foto 055 nivel 3, pasó a `suficiente` tras sumar el producto visible en ambos extremos. La comprobación final también corrigió otros casos cuyo stock del propio estante ya se veía entre los barrotes del carro: el lote queda con 299 niveles `suficiente` y 9 `no_evaluable`.

La revisión técnica está completada por Codex y los tres trabajos pasaron a la etapa de validación del equipo. Este cierre no certifica una validación humana independiente. El inventario conjunto de 296 imágenes está preparado para seleccionar particiones; no se asignaron particiones ni se inició entrenamiento.

## Respuesta recomendada en producción

Conservar las tres clases por nivel. Si el sistema no consigue una localización fiable para emitir una recomendación, devolver «captura no evaluable; repetir foto», mediante una regla de salida. Esto es una recomendación de comportamiento pendiente de implementar y probar; no se ha añadido una clase nueva ni se afirma que el sistema actual ya detecte todos esos fallos. La ausencia de detecciones no acredita que el stock sea suficiente.

## Referencias

- [DanceTrack, CVPR 2022, sección 3.1](https://openaccess.thecvf.com/content/CVPR2022/papers/Sun_DanceTrack_Multi-Object_Tracking_in_Uniform_Appearance_and_Diverse_Motion_CVPR_2022_paper.pdf): conserva cajas completas bajo oclusión parcial y omite personas totalmente ocultas.
- [COCOA — Semantic Amodal Segmentation](https://arxiv.org/abs/1509.01329): anota la extensión completa de las regiones, incluidas las partes ocultas.

La adopción de estos criterios para espacios de góndola es una decisión de este proyecto, no una norma publicada específica de retail. Un objetivo amodal no garantiza que cualquier nivel totalmente invisible pueda recuperarse a partir de una sola foto.
