# Modelo actual de Walmart Visión

**V3-YOLO26**, integrado en la aplicación y disponible en la [release publicada el 26 de octubre de 2026](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-10-26).

## Identidad y función

| Campo | Valor |
|---|---|
| Arquitectura | YOLO26n-seg |
| Clases | Una: `Nivel` |
| Checkpoint operativo | `best.pt` |
| Ensayo fuente | `v3_afinado_papeles_huevos_20261026_011847_7021` |
| SHA-256 del modelo | `6617f6dc7b20eac2e343b17813a1180c6df6c481f3fc8cb744bb3949ff18b2c9` |
| Uso en la app | Máscaras originales, confianza fija 0,60 y resolución 640 |

El modelo localiza áreas de niveles. No clasifica directamente reposición, personas u oclusiones. La app calcula e interpreta la ocupación por separado.

## Entrenamiento vigente

El último afinado partió de pesos propios V3 y utilizó **113 fotos: 67 reales y 46 sintéticas**. La selección reúne **32 superiores vacíos, 11 tomas reales nuevas, seis fotos de huevos y 64 de repaso**. El repaso cubre las 26 escenas de entrenamiento anteriores.

Configuración: AdamW, tasa de aprendizaje 0,0001, tamaño 640, batch 2 y semilla 42. Terminó tras **29 épocas**, con paciencia 10. El entrenador eligió el best de la **época 19** por fitness combinado de cajas y máscaras; el máximo mAP de máscaras del CSV estaba en la época 14.

## Datos y validación

El catálogo actual contiene **469 imágenes: 192 reales y 277 sintéticas**. La partición por escenas y familias es **337 train / 69 val / 63 test**. Una train está desactivada: hay 336 exportables, de las que el afinado seleccionó 113.

La validación del afinado contiene **22 reales y 47 sintéticas**, evaluadas por separado. El test conserva sus **63 fotos reservadas**, sin utilizarse para entrenamiento, selección o ajustes.

| Segmentación de máscaras | 22 fotos reales | 47 fotos sintéticas |
|---|---:|---:|
| mAP50 | 99,50 % | 99,46 % |
| mAP50–95 | 88,96 % | 85,33 % |

Estos resultados evalúan la delimitación de niveles, no el porcentaje de ocupación ni la precisión de reposición. El afinado fue adoptado tras revisión visual con limitaciones aceptadas: no se presenta como una mejora global frente al padre. En la validación común, el mAP50–95 de máscaras bajó de 90,49 a 88,96 % en reales y de 86,01 a 85,33 % en sintéticas.

[Resumen numérico y procedencia](Estado_V3_actual.json).

## Comportamiento de la app

- Modelo único, análisis de niveles y bordes, confianza fija 0,60.
- Ocupación experimental: combinación 70/30 de superficie y cobertura horizontal, con umbral 30 %.
- Confirmación manual de visibilidad; sin detección automática de personas u obstáculos.
- Recorte: solo zona visible y Revisar. Objeto delante: medición suspendida. Persona tapando: Góndola tapada, sin contornos ni ocupación.
- Señal concentrada en la mitad superior o periférica sin respaldo central e inferior: Revisar · señal ambigua, sin porcentaje presentado. Es una abstención experimental, no detección de carteles o vacío.
- La mediana es un criterio de anotación; no se fuerza durante la predicción.

## Limitaciones que permanecen

En la familia `le_g10`, a confianza 0,60, el superior vacío de la foto 029 se delimita demasiado alto y el de la 030 se omite. Faltan escenas independientes de papeles y huevos para evaluar generalización.

La entrada prevista son fotografías frontales o casi frontales; no existe corrección automática de perspectiva. La ocupación sigue sin calibración V3. La última ampliación de abstención se comprobó en 151 fotos de desarrollo y 754 detecciones, conservando las métricas brutas y añadiendo 35 revisiones; no constituye una evaluación exhaustiva ni prueba final. El procedimiento Docker ya fue probado correctamente por Vicente en macOS con la release anterior; esta entrega conserva ese flujo y sus dependencias.

[Manual](Usar_Walmart_Vision.md) · [Funcionamiento](Guia_para_entender_el_proyecto.md) · [Distribución](../Entregables/README.md)
