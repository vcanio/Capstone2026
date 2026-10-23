# Tarea 24: consistencia del nivel superior

Corrección solicitada por el usuario el 22 de octubre de 2026 en la [tarea 24 de CVAT](https://pcvicen.tailca514b.ts.net/tasks/24). Se revisaron visualmente sus **60 imágenes** y se conservaron los **308 polígonos y sus IDs**.

- **36 superiores abiertos corregidos:** se identificó el apoyo sobre el portaprecio en cada imagen y se proyectó la mediana de las alturas centrales de todos sus inferiores del mismo módulo, sin redondear. Las barandas, los carteles y la altura de los productos no se usaron como apoyo o techo.
- **24 superiores con techo físico claro:** su geometría se conservó exactamente y no se sustituyó por una altura calculada. Entre ellos está el caso con solo dos inferiores; no requiere una excepción a la regla de mediana porque tiene cubierta real.
- **248 inferiores conservados exactamente**, incluidas coordenadas, atributos y oclusión. Mantienen su delimitación pendiente; esta revisión no los aprueba para entrenamiento.
- **Todas las marcas Occluded se conservaron**, también las de los superiores. No se crearon ni eliminaron formas, tags o tracks ni se cambiaron los estados o etapas de los trabajos 60, 61 y 62.

Los 60 superiores tienen su delimitación revisada: **59 completa y 1 parcial**. El superior de `lider_express_010_D_persona.png`, frame 10, excede el borde superior del encuadre. Se recortó su polígono a la imagen y se conserva la proyección completa en el plan. No se reduce la mediana para hacerlo caber.

## Evidencias

- [Plan por imagen](plan.json): ID, referencias, alturas, mediana, apoyo, geometría anterior y posterior, cubierta física y recorte.
- [Verificación posterior de CVAT](verificacion.json): igualdad exacta con el plan, conservación de IDs, oclusiones y hashes de los inferiores.
- [Comprobación final y sincronización de la guía](comprobacion_final.json): el 23 de octubre se confirmó que las anotaciones seguían coincidiendo con la corrección y se actualizó la guía del proyecto, sin volver a escribir polígonos.
- [Superiores leídos de CVAT después de corregir](superiores_verificados.json).
- Vistas: rojo indica el superior anterior, verde el resultado y azul los inferiores conservados. [Frames 00–05](contacto_01.jpg), [06–11](contacto_02.jpg), [12–17](contacto_03.jpg), [18–23](contacto_04.jpg), [24–29](contacto_05.jpg), [30–35](contacto_06.jpg), [36–41](contacto_07.jpg), [42–47](contacto_08.jpg), [48–53](contacto_09.jpg), [54–59](contacto_10.jpg).

Respaldo privado anterior, solicitudes y respuestas, lecturas posteriores y programas: `.resguardo/superiores_t24_20261022`. La lectura posterior de cada trabajo y la de la tarea completa coincidieron con el plan. La corrección de geometría y del atributo administrativo no certifica revisión humana independiente ni habilita entrenamiento.

Esta revisión sustituye el estado anterior de superiores pendientes. La demostración visual de tres ejemplos preparada antes de esta corrección era una propuesta y no había escrito en CVAT. **La corrección aquí documentada sí está aplicada.** No se modificaron las anotaciones de las tareas V2 19/22 ni las de las tareas V3 27/28.
