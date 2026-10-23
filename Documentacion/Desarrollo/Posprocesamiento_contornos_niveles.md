# Posprocesamiento geométrico de los contornos de nivel

**Fecha:** 22 de octubre de 2026. **Estado:** implementado en el código local del
panel y de Walmart Visión; paquete de prueba independiente. La release publicada
con anterioridad conserva su contenido. No se entrenaron nuevos modelos.

## Problema y decisión

El criterio de anotación utilizado por el equipo en CVAT representa los niveles
con cuatro vértices y lados rectos. En la fotografía, la perspectiva puede hacer
que un nivel rectangular se vea como un trapecio u otro cuadrilátero.

YOLO de segmentación predice una máscara de píxeles. Anotar cuatro vértices
enseña la forma esperada, pero no impone una salida con cuatro esquinas. Al
extraer el contorno de la máscara pueden aparecer escalones, entrantes y
salientes, incluso cuando el nivel está localizado correctamente.

Se incorpora un **ajuste geométrico para la visualización**: obtener un
cuadrilátero convexo próximo al contorno predicho, conservando la perspectiva.
Esta decisión utiliza una propiedad del objeto definida por el criterio de
anotación; no consulta las etiquetas de referencia durante la inferencia.

## Qué cambia y qué se conserva

| Elemento | Tratamiento actual |
|---|---|
| Contorno visible y relleno de la región en la imagen de niveles | Se dibuja el cuadrilátero aceptado. |
| Posición del rótulo | Se calcula sobre el contorno que se dibuja. |
| Máscara original de YOLO | Se conserva sin modificar. |
| Clase, confianza, cantidad de detecciones y numeración | Se conservan. El ajuste no añade ni elimina detecciones. |
| Ocupación por bordes, color y textura | Sigue usando la máscara original. Sus mapas pueden diferir del borde ajustado. |
| IoU contra anotaciones y métricas de evaluación | Siguen usando las máscaras originales. No se recalculan resultados históricos con la forma ajustada. |
| CVAT, dataset, particiones y pesos | No se modifican. |

Los campos `display_polygon` y `contour_adjusted` registran el polígono de
presentación y si se aceptó el ajuste. `contorno_valido` en el panel sigue
describiendo el contorno original, no la validez del cuadrilátero mostrado.
En el panel, el ajuste se aplica a modelos reconocidos como niveles; el piloto
de módulos conserva su visualización anterior.

## Implementación y criterios de aceptación

La implementación compartida está en
[`geometria_niveles.py`](../../Herramientas/Modelos/geometria_niveles.py), función
`level_quadrilateral(points, size)`.

1. Verifica que el contorno tenga área y coordenadas finitas.
2. Calcula su envolvente convexa y busca una aproximación de cuatro vértices
   mediante `approxPolyDP`. Si no la obtiene, propone un rectángulo rotado con
   `minAreaRect`.
3. Propone también un refinamiento: muestrea el borde por longitud, ajusta cuatro
   rectas con `fitLine` y pérdida robusta Welsch, e intersecta rectas consecutivas.
4. Limita las esquinas al interior de la imagen y comprueba convexidad y área.
5. Compara los candidatos con el contorno original rasterizado y selecciona el
   de mayor coincidencia entre los que superan las comprobaciones.

El área del candidato debe estar entre **0,5 y 1,8 veces** la del contorno
original. La **IoU interna debe ser mayor que 0,55**, calculada en un lienzo de
384 × 384 píxeles con escala uniforme y espacio para ambas formas. Estos valores
son reglas de aceptación de esta implementación, pendientes de validación en un
conjunto amplio; no son umbrales calibrados de exactitud.

**La IoU interna compara dos salidas del sistema; no compara con CVAT y no mide
precisión contra la referencia.** Si no hay candidato aceptable, se conserva el
contorno original. Por tanto, el sistema no garantiza cuatro vértices para toda
predicción posible.

El dibujo se integra en
[`panel_worker.py`](../../Herramientas/Modelos/panel_worker.py) y
[`inferencia.py`](../../Herramientas/Demo_lite/inferencia.py). El
[`empaquetador`](../../Herramientas/Modelos/empaquetar_demo_lite.py) copia el módulo
compartido al paquete independiente y los archivos Docker lo incluyen.

## Verificación realizada y alcance

Se usó `lider_express_014_0_original.jpg`, fotografía conocida de validación V2
que originó las capturas revisadas, con **V2-YOLO26**, confianza **0,60**, IoU de
NMS **0,70**, tamaño de inferencia **640** y máscaras a resolución original
(`retina_masks=True`). Se aplicó la orientación EXIF antes de inferir.

- Se aceptaron **6 ajustes de 6 detecciones**, cada uno con cuatro vértices.
- La comparación antes/después reutilizó la misma predicción. Se comprobó que
  clase, confianza, identificadores y número de detecciones no cambiaran.
- Se revisó visualmente la comparación de los niveles 3 y 1 y se conservó la
  imagen completa del resultado.
- Pasaron **21 pruebas técnicas**: cuatro de geometría, quince de la aplicación
  y dos de integración del panel. Cubren perspectiva, salientes, coordenadas
  límite, entradas degeneradas y conservación de la predicción y de la entrada
  al cálculo de ocupación.
- El ZIP se extrajo y comprobó de forma independiente: cuatro modelos
  disponibles e inferencia real con seis contornos ajustados. Esa comprobación
  no acredita una instalación nueva en otro computador ni una ejecución Docker.

El [registro de evidencia](../Evidencias/posprocesamiento_contornos_20261022.json)
identifica fuentes y resultados. Las imágenes, JSON detallados y el ZIP de prueba
se conservan localmente en `Experimentos/Contornos/cuatro_vertices_20261022/`.
Los resultados ya guardados en el panel mantienen su dibujo anterior; hay que
analizar de nuevo la foto para generar la nueva visualización. Un servicio que
use una copia antigua del código debe actualizarse y reiniciarse sin trabajos
activos.

Estas comprobaciones verifican funcionamiento y una mejora visual en un caso
conocido. **No demuestran una mejora de mAP, IoU contra CVAT, clasificación u
ocupación**, ni constituyen una evaluación sobre imágenes independientes.

Para repetir las 21 pruebas técnicas desde la raíz del proyecto en PowerShell,
con el entorno local preparado:

```powershell
New-Item -ItemType Directory -Force .tmp/pruebas_contornos | Out-Null
$env:TEMP = Join-Path (Get-Location) '.tmp/pruebas_contornos'
$env:TMP = $env:TEMP
$env:PYTHONPATH = 'Herramientas/Modelos;Herramientas/Modelos/tests;Herramientas/Demo_lite'
& ./.venv-modelo/Scripts/python.exe -m unittest test_geometria_niveles test_lite.LiteTests test_ocupacion_paulo.SignalTests.test_worker_passes_original_pixels_even_while_rendering_red_yolo_mask test_ocupacion_paulo.SignalTests.test_worker_dispatches_weighted_v2_without_changing_yolo -q
```

Este comando ejecuta las pruebas seleccionadas; no corresponde a la suite
completa del proyecto ni repite la inferencia real del paquete.

## Justificación metodológica y evaluación pendiente

El posprocesamiento es una etapa explícita del sistema. OpenCV ofrece
[aproximación de contornos, ajuste de rectas y rectángulos rotados](https://docs.opencv.org/4.13.0/d3/dc0/group__imgproc__shape.html);
Ultralytics documenta las
[máscaras y sus polígonos de salida](https://docs.ultralytics.com/reference/engine/results/).
Usar esas operaciones es compatible con el proyecto siempre que se declare la
transformación y se distingan sus resultados de la salida original del modelo.

Un contorno más limpio puede seguir mal ubicado. El ajuste no recupera niveles
omitidos, no separa niveles fusionados ni corrige estados incorrectos. En casos
de oclusión, recorte o geometría ambigua, imponer cuatro lados puede incluir
áreas que no correspondan al criterio de anotación; requiere revisión.

Para evaluar una mejora de localización, se deben fijar el algoritmo y sus
parámetros usando desarrollo, y comparar **máscara original y cuadrilátero
ajustado contra las mismas anotaciones**, incluyendo casos favorables y fallos.
Registrar IoU contra referencia, ajustes rechazados y casos que empeoran. La
reserva final se utiliza después de fijar los parámetros y no se emplea para
retocarlos por fotografía. Si se adopta el cuadrilátero para medir ocupación,
esa modificación requiere su propia evaluación porque cambia la región medida.

## Texto para citar en el informe

> Se aplica un posprocesamiento geométrico que ajusta los contornos predichos a
> cuadriláteros, de acuerdo con el criterio de anotación de los niveles y
> conservando la perspectiva. El ajuste se utiliza para la visualización; la
> evaluación del modelo y la estimación de ocupación conservan las máscaras
> originales de YOLO. La comprobación inicial verifica el funcionamiento y la
> presentación, sin acreditar una mejora de precisión sobre un conjunto
> independiente.
