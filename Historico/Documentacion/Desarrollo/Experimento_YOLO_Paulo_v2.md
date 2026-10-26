> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Experimento V2: niveles YOLO + señal de detección de bordes

20 de octubre de 2026. Primera integración ejecutable, sin reentrenar ni cambiar
las etiquetas de los modelos existentes.

**Actualización · revisión 2:** se integró el script de detección de bordes actualizado (color con
brillo mínimo y textura en zonas oscuras). El fondo negro liso ya no se considera
ocupado por ser oscuro. El panel muestra «Revisión 2 · color y textura» al ejecutar
un análisis nuevo. Los resultados anteriores conservan sus parámetros y método.
Ver [revisión y comparación antes/después](../../../Laboratorio/Experimentos/Bordes/REVISION_20261020.md).

## Propósito y flujo

La foto entra a YOLO11 o YOLO26 V2. YOLO entrega una máscara y un estado por nivel.
El adaptador aplica las señales de detección de bordes y color dentro de cada máscara.
El resultado conserva el estado de YOLO y añade porcentajes experimentales y un
mapa amarillo de las celdas activadas.

El mapa de señal de cada análisis nuevo muestra, junto al número del nivel,
el porcentaje de ancho con señal y el de área con señal. Ambos llevan la
indicación «señal experimental»; no representan confianza YOLO ni un conteo de
productos. Si falta una medición se escribe «Sin medición», en lugar de 0 %.

En el panel: **V2 → Probar una foto → elegir modelo → Método de análisis →
YOLO + detección de bordes · experimental → Analizar foto**. Se puede usar una foto
de desarrollo o una propia. Elegir YOLO solo permite comparar la misma toma.
La combinación es un método de análisis dentro de V2; no es un nuevo modelo
entrenado ni una versión nueva del criterio de anotación.

Cada análisis combinado nuevo guarda en `Laboratorio/Experimentos/panel_pruebas/<id>/`:
`paulo_bordes.png` (bordes de toda la foto), `paulo_bordes_niveles.png`
(bordes filtrados dentro de las máscaras medibles, con margen interior) y
`paulo_senal.jpg` (mapa amarillo de señal). Los dos PNG son imágenes en escala
de grises, sin rellenos ni etiquetas de YOLO. Se abren en el resultado del panel,
en **Ver solo los bordes**. Las ejecuciones anteriores conservan sus archivos
originales; hay que analizar de nuevo para generar estos PNG.

## Qué se reutiliza y qué se adapta

La entrada del análisis de bordes es una copia de los píxeles RGB originales tomada antes de
la inferencia y del dibujo. Las máscaras solo delimitan dónde medir; el relleno
rojo o verde de YOLO se dibuja en otra capa para mostrarlo. Cada nueva ejecución
guarda `input_kind` e `input_rgb_sha256` en su procedencia. Una prueba del worker
verifica que una foto blanca con una visualización YOLO roja conserva 0 % de señal
para el análisis de bordes y el mismo hash de los píxeles originales.

El [original del 18 de octubre](../../../Laboratorio/Experimentos/Bordes/Versiones/gondola_bordes_20261018.py)
y el [nuevo script recibido de Paulo](../../../Laboratorio/Experimentos/Bordes/Versiones/gondola_bordes_paulo_20261020.py)
se conservan sin editar. La entrada [gondola_bordes.py](../../../Laboratorio/Experimentos/Bordes/gondola_bordes.py)
contiene la revisión ejecutable con validación de cajas y salida de mediciones.
Se importan sus funciones de mapa de bordes y eliminación de líneas.
La capa [ocupacion_paulo.py](../../../Laboratorio/Modelos/ocupacion_paulo.py) añade:

- Máscaras automáticas de YOLO, sin dibujar cajas manualmente.
- Normalización de la foto a un máximo de 1600 píxeles por lado, sin ampliarla.
- Margen interior de máscara y exclusión del exterior del cálculo y denominador.
  El exterior no se pinta de negro para analizarlo.
- Densidad de bordes, color y textura calculada sobre el área válida de cada celda.
  En revisión 2 se usa saturación con brillo mínimo 50 y desviación de brillo
  mayor que 4 en celdas de brillo medio menor que 90; oscuridad sola no activa señal.
- Rejilla de 24 píxeles, Canny 40/120 y filtros de color del prototipo.
  La longitud de las líneas se refiere al ancho del nivel; son parámetros
  iniciales fijados para esta pasada, no optimizados con la validación.
- Área con señal: fracción ponderada de las celdas válidas activadas.
- Ancho con señal: fracción de columnas válidas activadas en al menos dos filas
  y al menos el 15 % de sus filas válidas. Se proyecta sobre el eje horizontal de
  la foto; todavía no hay rectificación de perspectiva.
- Ausencia de medición ante máscara ausente, desalineada, no binaria, vacía, resolución insuficiente
  o estado no evaluable. No se sustituyen esos casos por 0 %.

**Corrección de máscaras · 20 de octubre:** el análisis usa directamente la máscara
binaria de YOLO. Un defecto del polígono de visualización ya no descarta un nivel
cuya máscara es utilizable. No se repara ni se reemplaza por un rectángulo; se
conservan sus píxeles y el margen interior. La procedencia registra
`mask_policy: yolo_raster_v1` y cada medición registra `mask_source` y
`contour_warning`. La validez del polígono sigue disponible como diagnóstico.
En `lider_express_046_A_vacios`, el nivel inferior había sido omitido por esa
comprobación. Los resultados históricos descritos a continuación conservan la
política anterior y no se sobrescriben.

Verificación con la misma foto, YOLO26 y confianza mínima 0,6:
`Laboratorio/Experimentos/panel_pruebas/660eddd95e624ac282e8e76b9d50bbec/resultado.json`.
El nivel 1 pasa de sin medición a medido: 74,84 % de área con señal y 96,88 %
de ancho con señal (valores experimentales). El mapa filtrado ahora incluye sus
productos. Los cinco niveles mantienen exactamente sus clases, confianza,
alertas y métricas YOLO frente al análisis anterior. Las 51 pruebas de integración,
interfaz y validación pasaron; incluyen un polígono cruzado con máscara utilizable
y rechazo de máscaras vacías, desalineadas, no binarias y con valores no finitos.

El área y ancho se calculan sobre la región visible de la máscara. No estiman
cantidad de unidades, profundidad ni contenido oculto. Un producto al fondo
puede generar señal si es visible, pero el algoritmo no sabe por sí solo si un
borde pertenece a un producto o al fondo de la góndola. La revisión 1 contaba
oscuridad como presencia; la revisión 2 corrige ese caso uniforme. Los fondos
con color o textura, rieles, carteles y reflejos todavía pueden generar señal.

## Qué significa la primera comparación

Esta sección conserva la primera pasada histórica. La revisión 2 se comprobó
de nuevo sobre las mismas fotos de desarrollo; no constituye una prueba final
independiente de los cambios decididos durante el desarrollo.

Se ejecutan los dos modelos sobre las mismas 10 fotos reales de validación de la
partición base registrada. Se verifican sus referencias y los hashes de las fotos
y etiquetas exportadas. No se accede a las fotos de evaluación final ni se ajustan
parámetros usando sus resultados. Las variantes IA ya validadas conservan sus
particiones; no se solicita repetir su validación.

Se guardan el estado YOLO, referencia humana emparejada por IoU, confianza YOLO,
área y ancho con señal, motivos de ausencia de medición y las visualizaciones.
Los porcentajes no cambian las alertas del modelo. El umbral humano del 30 %
no se aplica automáticamente a una grilla de bordes/color.

La anotación `reponer/suficiente` es una referencia de estado, no una medición
numérica de ocupación. Permite revisar coherencia y errores por estado, pero no
calcular el error del porcentaje. Para afirmar mayor precisión de ocupación,
la siguiente etapa requiere una muestra con referencias numéricas de ancho
visible y revisión de los mapas de señal, especialmente fondos oscuros y productos
bajos. Tampoco se presenta la revisión humana como eliminada por esta combinación.

## Evidencia reproducible

El primer informe queda en
`Laboratorio/Experimentos/Bordes/combinado_v2_20261020_primera_pasada/`:

- `experimento.json`: configuración fijada, partición y hashes del código.
- `entorno.json` y `fuentes/`: versiones utilizadas y copias verificadas del código de esta pasada.
- `resumen.json`: métricas YOLO y distribución exploratoria de señales por estado.
- `informe.html`: comparación visual de ambos modelos, por foto y por nivel.
- Una carpeta por modelo con `niveles.csv`, `resultados.json` y diez comparativas.

El informe mide funcionamiento de la conexión y comportamiento de la señal.
La precisión del estado sigue siendo la de YOLO en esta fase.

### Resultado observado en la primera pasada

| Modelo | Estados correctos / 51 referencias | Falsas alertas | Detecciones con señal medible |
|---|---:|---:|---:|
| YOLO11 V2 | 48 / 51 | 4 | 43 / 59 |
| YOLO26 V2 | 50 / 51 | 0 | 36 / 55 |

Los casos sin señal medible corresponden a contornos poligonales que requieren
revisión (16 con YOLO11 y 19 con YOLO26). El estado de YOLO se conserva, pero el
adaptador se abstiene de medir esos recortes. Esto no añade una clase al modelo.

En `lider_express_040_0_original.jpg`, el nivel 5 de YOLO11, emparejado con una
referencia `reponer`, recibió **94,64 % de área con señal y 100 % de ancho con
señal**. El mapa muestra activación extensa en el fondo oscuro de esa región.
Con YOLO26, la detección correspondiente no se mide por su contorno inválido.

Este resultado impide afirmar que la combinación ya mejora la ocupación: la
regla de oscuridad necesita distinguir fondo de producto. La siguiente iteración
debe resolver ese error y ampliar la cobertura de máscaras válidas. No procede
convertir la señal actual en un reemplazo de las alertas de YOLO.

Para repetir, usar una carpeta nueva de salida:

```powershell
docker exec walmart-modelos-panel_modelos-1 python /app/Herramientas/Modelos/experimentar_paulo.py --runs v2_base_yolo11n_01_20261020_002800_ec8d v2_base_yolo26n_01_20261020_004933_b105 --out /app/Experimentos/Bordes/combinado_v2_nueva_pasada
```

Código del experimento:
[experimentar_paulo.py](../../../Laboratorio/Modelos/experimentar_paulo.py).
Los resultados del panel también conservan método, parámetros y hashes del
adaptador y del original de Paulo en su `resultado.json`.
