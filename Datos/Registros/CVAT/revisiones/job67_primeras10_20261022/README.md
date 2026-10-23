> **Prueba histórica retirada / vista previa fuera del dataset.** El 23/10/2026 sus imágenes de revisión se trasladaron al archivo local `.resguardo/orden_registros_20261023/vistas_pruebas_retiradas/job67_primeras10_20261022/`. Los planes, coordenadas, verificaciones y reversiones permanecen aquí. Las cifras e instrucciones siguientes describen aquella prueba, no el estado vigente.

# Prueba V3 · primeras 10 imágenes del trabajo 67

**RETIRADA A PETICIÓN DEL USUARIO.** Los 40 polígonos del asistente fueron eliminados y verificados. Los planes y las imágenes siguientes documentan exclusivamente la prueba histórica; no son las anotaciones vigentes. [Verificación de reversión](reversion.json). El usuario marcará los inferiores y avisará para calcular únicamente el superior.

[Abrir en CVAT desde la primera foto](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/67?frame=0).

Se anotaron `lider_2_001_0_original.jpg` a `lider_2_010_0_original.jpg`, frames 0–9, con **40 polígonos de la clase Nivel**. Son cuatro áreas del módulo central completo en cada foto. Los módulos laterales recortados y el fondo quedan fuera del tramo objetivo de esta prueba.

Se trazaron manualmente **30 áreas inferiores** siguiendo los estantes y su perspectiva, sin usar el ancho de los pilares ni ajustar los contornos a los productos. Las diez zonas superiores no tienen cubierta física que las cierre por arriba; la franja azul y la cartelería son del fondo. Se proyectaron **10 áreas superiores** desde el borde superior del nivel inmediato inferior, usando la mediana de las tres alturas disponibles y conservando las x y la pendiente de ese borde.

Las coordenadas de CVAT corresponden a imágenes orientadas de 3000 × 4000. Se revisaron individualmente las diez fotografías y las superposiciones. Después de la carga se leyeron los 40 polígonos de CVAT para verificar coordenadas, clases, atributos, número de niveles y cálculo de la mediana. No se modificaron los frames 10–121 ni los trabajos 68 y 69.

`delimitacion=completa` indica que la región se delimitó completa, incluida la proyección convencional. **No significa aprobación humana ni habilitación de entrenamiento.** La anotación y la revisión visual son del asistente y requieren validación del usuario. No se marcaron estados de disponibilidad ni se completó el trabajo de 41 imágenes.

- Revisión visual 001–005 (vista archivada localmente: `contactos_1.jpg`).
- Revisión visual 006–010 (vista archivada localmente: `contactos_2.jpg`).
- [Coordenadas y medianas por foto](plan.json).
- [Verificación y enlaces a cada frame de CVAT](verificacion.json).
- [Regla de mediana](../../../../../Documentacion/Desarrollo/Regla_nivel_superior_mediana_V3.md).

Respaldo previo y resultado en `.resguardo/job67_primeras10_20261022T042841Z`. Tras revertir quedan **41 fotos sin anotar en el trabajo 67** y **122 en el lote**. Partición sin asignar y entrenamiento deshabilitado.
