# Entrenar niveles con el criterio nuevo

El script `Herramientas/Modelos/entrenar_niveles.py` entrena YOLO de segmentación
con el criterio `disponibilidad_visual_nivel_v2_reponer`, descrito en la
[guía de Líder Express](Guia_anotacion.md).
Está comentado en español y usa las dependencias del laboratorio de modelos.

## Entorno compatible

El entorno local y Docker usan **Ultralytics 8.4.174**. El script rechaza otras
versiones con instrucciones para corregir la instalación, antes de iniciar un ensayo.
Instalar o sincronizar las dependencias desde la raíz del proyecto:

```powershell
& .\.venv-modelo\Scripts\python.exe -m pip install -r .\Herramientas\Modelos\requirements.txt
& .\.venv-modelo\Scripts\python.exe -m pip check
& .\.venv-modelo\Scripts\python.exe .\Herramientas\Modelos\entrenar_niveles.py --verificar-entorno
```

La última orden carga el YOLO26 de segmentación real sin entrenar. También acepta
`--modelo` para comprobar otros pesos. La configuración de YOLO y su fuente para
gráficas quedan en `.config-modelo/niveles_v2/`, separadas de los ajustes del panel
y del usuario. Se desactivan instalaciones automáticas e integraciones externas.
Si falta una fuente local en otro sistema, configurar `MODEL_FONT` con un `.ttf`.

| ID YOLO | Clase | Criterio de anotación |
|---|---|---|
| 0 | `Nivel_reponer` | Vacío o producto en menos del 30 % del ancho completo del nivel. |
| 1 | `Nivel_suficiente` | Producto en al menos el 30 % del ancho completo. |
| 2 | `Nivel_no_evaluable` | La visibilidad impide decidir el estado. |

El polígono delimita todo el espacio del nivel, incluidos los huecos. El umbral
del 30 % guía la anotación: el script aprende las clases anotadas, no calcula
automáticamente un porcentaje de ocupación. `no_evaluable` no equivale a reponer.

## Preparar el dataset

Se necesita un dataset YOLO de **segmentación**, anotado y revisado, con este formato:

```text
dataset_niveles_v2/
  data.yaml
  images/
    train/       # Fotos de entrenamiento
    val/         # Fotos de validación
    test/        # Opcional: escenas reales independientes para evaluación final
  labels/
    train/       # Un .txt por foto de entrenamiento
    val/         # Un .txt por foto de validación
    test/        # Si se proporciona el grupo test
```

Contenido de `data.yaml`:

```yaml
train: images/train
val: images/val
names:
  0: Nivel_reponer
  1: Nivel_suficiente
  2: Nivel_no_evaluable
```

También acepta los nombres simples `reponer`, `suficiente`, `no_evaluable`, en ese
mismo orden. Las rutas relativas, incluido un campo `path` opcional, se resuelven
respecto de `data.yaml`. Cada etiqueta contiene una línea por nivel:

```text
0 0.10 0.20 0.90 0.20 0.90 0.40 0.10 0.40
```

El primer número es la clase y el resto son pares de coordenadas x/y normalizadas
entre 0 y 1. Este ejemplo representa un nivel `reponer` con cuatro vértices.
No se admiten cajas de detección. Una foto sin niveles puede tener un `.txt` vacío.

Todas las clases necesitan ejemplos de entrenamiento y validación. Si hay un grupo
`test`, también se exige cobertura de sus clases. Para pruebas exploratorias se
puede usar `--permitir-validacion-incompleta`: emite advertencias y registra la
cobertura incompleta; no elimina el requisito de las tres clases en entrenamiento.
Las métricas de clases ausentes no permiten juzgar su desempeño.
Mantener originales, variantes y otras vistas de una misma escena en el mismo
grupo. El script detecta imágenes idénticas entre grupos y familias con los nombres
conocidos `lider_express_NNN_0_original` / `lider_express_NNN_A/B/C_...`;
la separación de otras vistas y escenas debe revisarse antes. El grupo `test` debe
contener escenas reales independientes, sin vistas o variantes usadas en desarrollo.
Se mantiene fuera de `train` y `val`: no interviene en el ajuste ni en la selección
de los mejores pesos. No reutilizarlo para elegir hiperparámetros.

La lista de extensiones se obtiene de la versión instalada de YOLO, incluyendo MPO,
AVIF y las demás que admita ese entorno. Cada imagen debe pasar verificación y
decodificación de Pillow y del cargador real de YOLO: al menos 10 × 10 píxeles y una
salida de tres canales uint8 del mismo tamaño. Se rechazan imágenes corruptas, JPEG
incompletos y orientación EXIF sin aplicar. No se reparan originales automáticamente.
Aplicar cualquier corrección de orientación también a las anotaciones. Un formato
reconocido por extensión que no pueda decodificarse falla con el archivo identificado.

**Estado actual:** la exportación revisada del panel sigue usando cuatro clases.
No sirve directamente para este script. Una exportación de CVAT que conserve solo
la clase `Nivel` tampoco sirve: hay que convertir el atributo `estado` en los IDs
anteriores. Este script recibe los datos ya preparados; no importa CVAT, no revisa
las anotaciones por una persona y no convierte el dataset anterior. La tarea 19
todavía necesita una partición por escenas y una exportación revisada compatible.

## Ejecutar desde la raíz del proyecto

En los comandos siguientes, `Datos/mi_dataset_niveles_v2/data.yaml` es un ejemplo:
reemplazarlo por la ruta del dataset preparado.

Primero comprobar los datos, sin entrenar ni crear una carpeta de ensayo:

```powershell
& .\.venv-modelo\Scripts\python.exe .\Herramientas\Modelos\entrenar_niveles.py --data .\Datos\mi_dataset_niveles_v2\data.yaml --solo-verificar
```

Iniciar un ensayo con YOLO26 nano de segmentación y selección automática de GPU/CPU:

```powershell
& .\.venv-modelo\Scripts\python.exe .\Herramientas\Modelos\entrenar_niveles.py --data .\Datos\mi_dataset_niveles_v2\data.yaml --nombre YOLO26_niveles_v2_01 --epochs 100 --imgsz 640 --batch 2
```

Para usar YOLO11, añadir `--modelo .\Modelos\preentrenados\yolo11n-seg.pt`.
Para CPU, añadir `--device cpu`; para la primera GPU, `--device 0`.
Se puede iniciar otro ensayo desde un `best.pt` de segmentación con `--modelo`:
es ajuste fino, no reanudación de un entrenamiento interrumpido.

Opciones de entrenamiento: `--epochs` (100), `--imgsz` (640), `--batch` (2),
`--lr` (0.001), `--patience` (20) y `--seed` (42).
Consultar todas con `--help`. Cada ensayo requiere un nombre nuevo.

Para una evaluación final, añadir `test: images/test` a `data.yaml`, preparar
`labels/test` y ejecutar con `--evaluar-test`. El script comprueba duplicados y
familias entre las tres particiones y solo evalúa los mejores pesos sobre `test`
después del entrenamiento y la validación. No usa métricas de test para elegirlos.
Aunque una partición no se solape por archivo, la independencia por escena debe
comprobarse al preparar el dataset.

## Augmentation y resultados

Aplica rotación de hasta ±3°, desplazamiento de hasta 5 %, escala entre 0.85 y 1.15
y variación de tono, saturación y brillo. Mosaic, MixUp, Copy-Paste, cizallamiento,
perspectiva y volteos están desactivados. Las transformaciones se aplican durante
el entrenamiento, sobre imagen y etiquetas; no generan archivos nuevos del dataset.

Los resultados se guardan en `Experimentos/niveles_v2/<nombre>/`:

- `data.yaml`: rutas resueltas y clases utilizadas.
- `dataset/`: copia independiente de imágenes y etiquetas revisadas, con su YAML.
- `revision_datos.json`: recuentos y hashes de imágenes y etiquetas.
- `configuracion.json` y `entorno.json`: ajustes, pesos iniciales y versiones.
- `entrenamiento/weights/best.pt` y `last.pt`: mejores y últimos pesos.
- `entrenamiento/`: configuración efectiva de Ultralytics, curvas y resultados.
- `validacion/` y `metricas_validacion.json`: evaluación de los mejores pesos.
- `alertas_val.json` y `por_imagen_val.json`: precisión, recall, F1, omisiones,
  falsas alertas, matriz de confusión y detalle por foto a confianza fija.
- Con `--evaluar-test`: los equivalentes `evaluacion_final/`,
  `metricas_evaluacion_final.json`, `alertas_test.json` y `por_imagen_test.json`.

Cada ensayo copia únicamente el inventario verificado y comprueba sus SHA-256 antes
de entrenar. No copia cachés de etiquetas `.cache` ni de imágenes `.npy`. Así no
reutiliza etiquetas anteriores aunque se hayan cambiado conservando su tamaño.
`cache=False` por sí solo no desactiva la caché de etiquetas de YOLO. Las cachés que
YOLO genere dentro del ensayo pertenecen a esa copia. Se vuelve a comprobar su
contenido al terminar y después de evaluar; si cambió, el script informa un error.
No modificar la copia interna mientras se ejecuta el ensayo. Conservarla junto con
los pesos para poder reproducir los datos utilizados.

El JSON de YOLO incluye métricas agregadas y un resumen por clase. Además, el
evaluador propio v2 mide cada estado y reposición por separado. Empareja referencias
y predicciones por IoU de máscara, sin exigir que la clase coincida. Usa confianza
0.25 e IoU mínimo 0.5 por defecto, configurables con `--conf` y `--iou-mascara`.
Estos parámetros deben fijarse con desarrollo y mantenerse para la evaluación final.

Un nivel `reponer` omitido o predicho como otro estado cuenta como reposición omitida.
Una predicción `reponer` sobre otro estado o sin referencia cuenta como falsa alerta.
`no_evaluable` no genera una alerta acertada. Los duplicados sin emparejar cuentan
como predicciones extra. Si no hay referencias o predicciones para calcular un
cociente, se guarda `null`, no un acierto perfecto. El emparejamiento es voraz por IoU;
puede ser ambiguo ante niveles muy superpuestos y conviene revisar esas fotos.

## Comprobaciones del código

Pruebas de validación, aislamiento del dataset y evaluación (desde la raíz):

```powershell
& .\.venv-modelo\Scripts\python.exe -m unittest discover -s Herramientas/Modelos -p "test_*niveles*.py"
```

Existe también una prueba real opcional que carga YOLO26, entrena una época en CPU
con figuras sintéticas, guarda `best.pt` y ejecuta validación y test. Para incluirla
en el comando anterior, definir `$env:RUN_NIVELES_REAL = '1'`. Usa archivos temporales;
verifica la integración del software, no la calidad predictiva sobre góndolas reales.
No representa un nuevo modelo del proyecto ni una evaluación de sus fotografías.

Verificación realizada el 19 de octubre de 2026 en el entorno local:

- Ultralytics 8.4.174, PyTorch 2.5.1+cu121; `pip check` sin dependencias rotas.
- Carga real de `yolo26n-seg.pt` correcta.
- Suite general: 183 pruebas ejecutadas, 182 aprobadas y la integración opcional omitida.
- Comprobación final de niveles con integración habilitada: 35 pruebas aprobadas,
  incluida una época real en CPU, guardado y recarga de `best.pt`, validación,
  evaluación de test y generación de los JSON de métricas y alertas.

Las figuras sintéticas de esta prueba no miden precisión sobre góndolas reales.
La calidad del modelo sigue pendiente de evaluación con datos anotados y escenas
independientes. El registro de la comprobación final queda en
`.tmp/verificacion_niveles_v2.log` (archivo local excluido de Git).

El script funciona por consola. El panel actual requiere adaptar su catálogo,
exportación, clases, colores y evaluación antes de integrar modelos de tres estados.
Por eso los ensayos nuevos quedan dentro de `Experimentos/niveles_v2/` y no aparecen
como modelos utilizables en ese panel.
