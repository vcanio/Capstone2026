# División de Líder Express · 19 de octubre de 2026

La asignación de **296 imágenes** está fijada en [particion.json](particion.json).
Los inventarios de ambos lotes tienen `grupo_escena` y `particion_modelo` aplicados.
No se movieron imágenes, no se modificó CVAT ni se inició entrenamiento. La reserva
histórica y las versiones anteriores de datos/modelos permanecen separadas.

## Primera etapa: niveles visibles

| Destino | Originales reales | Variantes A/B/C | Total base |
|---|---:|---:|---:|
| Entrenamiento | 40 | 120 | 160 |
| Validación | 10 | 30 | 40 |
| Evaluación final | 9 | 27 | 36 |
| Total | 59 | 177 | 236 |

La validación principal usa **solo los 10 originales reales**. Las 30 variantes
se usan como diagnóstico sintético separado. La evaluación final principal usa
los 9 originales reales; sus 27 variantes son un diagnóstico final adicional.
No sumar ambos tipos de métricas como si representaran fotos reales independientes.

Las listas de rutas, relativas a la raíz del proyecto, están en [listas](listas/).
`base_train.txt`, `base_val_real.txt` y `base_test_real.txt` definen el flujo
principal. Las listas `*_sintetica_diagnostico.txt` conservan su alcance separado.
La primera etapa aprende `reponer` y `suficiente`; no contiene ejemplos de
`no_evaluable` y no permite afirmar que reconoce ese estado.

## Segunda etapa: visibilidad limitada

| Destino reservado | Imágenes con obstáculos |
|---|---:|
| Entrenamiento posterior | 41 |
| Validación posterior | 10 |
| Evaluación final posterior | 9 |

Cada variante con carros, personas o cajas hereda el destino de su familia.
Sus listas tienen el sufijo `pendiente_revision`: asignar el destino no aprueba
la imagen ni sus anotaciones. La copia consultada tenía los trabajos 54/55/56 en
etapa de validación y 308 niveles: 299 suficientes y 9 no evaluables, sin reponer.
Estos conteos son provisionales y reemplazan únicamente como referencia la copia
anterior de 256/41/11; no se reescribieron los registros históricos de revisión.

Después del cierre, incorporar solo las 41 variantes de entrenamiento al modelo
de la segunda etapa. Las 10 de validación sirven para desarrollo. Las 9 finales
se conservan hasta congelar las versiones que se quieren comparar.

La prueba inicial del modelo base sobre obstáculos debe usar el bloque de
validación. No recorrer el bloque final para ajustar el método de Paulo, elegir
umbrales ni decidir qué modelo conservar. Comparar las versiones finales sobre
la misma evaluación reservada al terminar el desarrollo.

## Escenas y familias

Se revisaron visualmente los 59 originales, con evidencia en las tres hojas de
contacto de [fuentes](fuentes/). [grupos_escena.json](grupos_escena.json) documenta
19 grupos conservadores, con motivos por grupo. Se agrupan vistas repetidas y
algunos tramos vecinos para reducir filtración; no se presenta cada grupo como
una identidad física confirmada por el fotógrafo. No se consultaron predicciones.

- Validación: familias **014–016, 026–028 y 039–042** (10 familias, 3 grupos).
- Evaluación final: familias **006–010 y 051–054** (9 familias, 2 grupos).
- Entrenamiento: las **40 familias restantes**, agrupadas en 14 grupos.

El reparto base es aproximadamente 68/17/15 por imágenes, próximo al objetivo
70/15/15 sin romper grupos. El número de escenas independientes es menor que el
de familias: especialmente, nueve originales finales pertenecen solo a dos grupos.
La división mide separación dentro de una captura/local, no generalización entre
supermercados o sesiones independientes. Si después se descubre solapamiento entre
grupos, crear una nueva versión antes de entrenar; no mover fotos silenciosamente.

## Cobertura y pendientes

La captura actual de la tarea 19 tiene 1.212 polígonos, todos con estados válidos:
801 suficientes y 411 reponer; los trabajos 45/46/47 están completados.
Las comprobaciones geométricas no detectaron polígonos inválidos, duplicados
exactos ni fotos sin niveles. Esto no sustituye la revisión semántica humana.

| Niveles de referencia | Entrenamiento | Validación | Evaluación final |
|---|---:|---:|---:|
| Suficiente, todas las imágenes base | 538 | 135 | 128 |
| Reponer, todas las imágenes base | 278 | 69 | 64 |
| Suficiente, solo originales reales | 202 | 50 | 47 |
| Reponer, solo originales reales | 2 | 1 | 1 |

Solo hay **cuatro niveles reales reponer**, en las familias 040, 049, 050 y 051.
Los grupos que los contienen se reparten para dejar cobertura real en los tres
destinos. Un único caso en validación/test no permite una estimación robusta de
detección de faltantes. Faltan casos reales independientes, incluyendo vacíos y
poco stock, y casos reales no evaluables. Las métricas sintéticas serán auxiliares.

El estado reponer no distingue vacío de poco stock: su cobertura por separado
sigue pendiente de auditoría humana. No se dedujo de A/B/C ni se añadieron campos
al formulario de CVAT. Por este pendiente, la revisión de visibilidad aún abierta
y la exportación v2 por completar, `aprobado_entrenamiento` sigue en `false`.

## Reproducción y verificación

Se guardaron copias de tareas, etiquetas, metadatos y anotaciones leídas desde CVAT
en `fuentes/tarea_19.json` y `fuentes/tarea_22.json`, con SHA-256 en el registro.
Los registros anteriores a la aplicación se conservan solo en la carpeta local `respaldo_registros/`, excluida de Git y del empaquetado. No se necesita ese respaldo para verificar la partición: el repositorio conserva `particion.json`, las listas, los grupos y las fuentes registradas.
La partición verifica SHA-256 de las 296 imágenes, consistencia con los frames y
separación de las familias y grupos entre destinos.

Desde la raíz del proyecto:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Herramientas/Datos/particionar_lider_express.py --verify
& ./.venv-modelo/Scripts/python.exe -m unittest discover -s Herramientas/Datos -p test_particionar_lider_express.py
```

La aplicación inicial se hizo con `--apply`. Una partición existente no se
sobrescribe. Cambios posteriores de anotaciones requieren una copia nueva que
respete esta asignación y actualice los conteos, sin reutilizar este registro
como si sus anotaciones ya hubieran cambiado.
