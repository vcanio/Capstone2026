# Walmart Lite — probar modelos con fotos propias

La entrega **Walmart_Lite_V2_Deteccion_Bordes_20261020.zip** contiene **YOLO11-1**, **YOLO26-1**, **V2-YOLO11** y **V2-YOLO26**, y una interfaz local para probar fotos con YOLO o YOLO + detección de bordes. No necesita el proyecto completo, CVAT, Docker, las imágenes de entrenamiento ni acceso al computador original.

## Otro PC con Windows

1. **Extraer todo el ZIP** a una carpeta local donde puedas guardar archivos. No ejecutar los archivos desde dentro del ZIP.
2. Abrir **iniciar.cmd**. La primera vez necesita Internet: descarga automáticamente un Python compatible y las dependencias dentro de esa misma carpeta. Después abre el navegador en **http://127.0.0.1:8095**.
3. Seleccionar o arrastrar una foto JPG, PNG o WebP, elegir un modelo y el método **YOLO + detección de bordes** o **Solo YOLO**, y pulsar **Analizar foto**. Mantener la consola abierta mientras usas el visor; Ctrl+C la detiene.

En el modo con bordes, además de las predicciones aparecen una tabla de señal por
nivel, **Ver mapa de señal** y **Ver solo los bordes**, con la fotografía completa
y los bordes filtrados dentro de las máscaras. El amarillo representa señal
experimental por bordes, color y textura; todavía no equivale al porcentaje real
de producto y no cambia el estado de YOLO. Los niveles sin máscara o no evaluables
se comunican como sin medición, en vez de asignarles un porcentaje cero.

**No necesitas instalar Python, desinstalar el que tienes ni cambiar de versión.** Puedes conservar Python 3.13 u otra versión para tus propios proyectos. Walmart Lite utiliza su propio Python 3.12 en `.runtime/python` y sus paquetes en `.entorno-py312`. No cambia PATH, el registro de Python de Windows ni paquetes globales. El instalador incluido es para Windows x64.

La primera preparación puede tardar varios minutos y ocupar bastante más espacio que el ZIP por PyTorch. Se muestra su avance y se conserva un registro en `.runtime/instalacion.log`. Si falla la conexión, vuelve a abrir iniciar.cmd: aprovecha lo que ya descargó. Los siguientes arranques reutilizan el entorno preparado y no vuelven a instalarlo. `instalar.cmd` permanece como opción para preparar el entorno por separado, pero ya no es un paso obligatorio.

Después de instalar las dependencias, las predicciones locales no requieren conexión a Internet. La aplicación escucha únicamente en este equipo. Las fotos se procesan en memoria: no se guardan ni se agregan a ningún entrenamiento. No se incluyen fotos del dataset en el ZIP.

Si el puerto 8095 está ocupado, cerrar otra instancia o ejecutar `iniciar.cmd --port 8096` desde esta carpeta. La primera predicción puede tardar más porque carga los pesos. La velocidad depende del equipo; el entorno automático usa CPU y no requiere tarjeta NVIDIA.

## Colab

1. Abrir [Google Colab](https://colab.research.google.com/), elegir **Archivo → Subir cuaderno** y seleccionar `Probar_en_Colab.ipynb`.
2. Opcionalmente seleccionar una GPU en **Entorno de ejecución → Cambiar tipo de entorno de ejecución**. La disponibilidad depende de Colab; el cuaderno también admite CPU.
3. Ejecutar las celdas en orden. Cuando lo solicite, subir el ZIP completo de Walmart Lite, seleccionar un modelo y subir una foto.
4. El cuaderno muestra la predicción, los recuentos y permite descargar la imagen. Para probar otra foto, repetir las últimas celdas.

En Colab, los pesos y las fotografías que selecciones se suben al entorno de Google para analizarlos allí. No se monta Google Drive, no se publica una web ni se genera un enlace público. Una sesión nueva requiere cargar otra vez los archivos. No se necesita volver a entrenar.

El cuaderno usa el mismo módulo de inferencia que la interfaz local, pero muestra los resultados dentro del cuaderno. Su ejecución requiere acceso a Colab; la prueba local del paquete no confirma disponibilidad de GPU ni compatibilidad de todas las versiones futuras de su entorno.

## Qué incluye y cómo interpretar el resultado

- `modelos/*.pt`: copias exactas de los cuatro `best.pt` conservados, con clases y procedencia por modelo.
- `modelos.json`: procedencia y SHA-256 de cada modelo; se comprueban al iniciar.
- `app.py`, `inferencia.py`, `interfaz.html`: visor independiente de inferencia.
- `ocupacion_paulo.py`, `gondola_bordes.py`: revisión 2 de detección de bordes, con procedencia y hashes en el manifiesto; se ejecuta sobre la foto original, sin colores dibujados por YOLO.
- `iniciar.cmd`, `preparar.cmd`, `preparar.py`, `requirements.txt`: preparación automática y arranque en Windows. `instalar.cmd` es opcional.
- `herramientas/uv.exe`, su procedencia y sus licencias: gestor oficial de Astral que prepara el Python privado; no se instala globalmente.
- `Probar_en_Colab.ipynb`: prueba de los mismos pesos en un cuaderno de Colab.

El criterio depende del modelo. V1 devuelve vacío, baja disponibilidad, suficiente o no evaluable. V2 base devuelve reponer y suficiente; no reconoce no evaluable. La leyenda y el resumen se adaptan al modelo seleccionado. Vacío y baja señalan posibles faltantes; no evaluable no equivale a vacío. La confianza es un puntaje del modelo, no un porcentaje de ocupación.

Una foto sin anotaciones permite observar predicciones; no mide precisión. La validación V1 no contiene vacíos ni bajos. La validación V2 contiene una sola referencia real reponer; todavía hace falta ampliar la evaluación independiente de alertas.

Límites de imagen: 15 MB, 24 megapíxeles, JPG/PNG/WebP sin animación. Se corrige la orientación y se limita el lado mayor a 4096 píxeles para acotar la memoria. La inferencia usa entrada de 640 px y NMS 0,7, como la demostración del panel.

## Versiones y otras plataformas

El entorno automático Windows fija Python 3.12, PyTorch 2.5.1 para CPU, torchvision 0.20.1, Ultralytics 8.4.174, NumPy 1.26.4 y Pillow 12.3.0. La verificación V2 está en VERIFICACION_V2.md del código y en VERIFICACION.md dentro del ZIP; el documento histórico VERIFICACION.md del código conserva las pruebas V1. El ZIP incluye el preparador, pero descarga Python y las bibliotecas durante el primer inicio; no es una entrega con instalación inicial sin Internet.

En Linux, usar Python 3.11/3.12, crear un entorno virtual, instalar PyTorch/torchvision para CPU con el mismo índice oficial y luego `pip install -r requirements.txt`. Iniciar con `python app.py --open`. Algunas distribuciones pueden requerir bibliotecas del sistema para OpenCV.

Fuentes: [Python administrado por uv](https://docs.astral.sh/uv/guides/install-python/), [predicción con modelos propios en Ultralytics](https://docs.ultralytics.com/usage/python/), [instalación CPU de PyTorch](https://pytorch.org/get-started/previous-versions/), [carga de archivos en Colab](https://colab.research.google.com/notebooks/io.ipynb), [recursos y límites de Colab](https://research.google.com/colaboratory/faq.html).

Ultralytics y PyTorch mantienen sus propias licencias y condiciones. Las dependencias se descargan de sus fuentes de distribución; el ZIP no redistribuye sus bibliotecas ni incluye una licencia comercial de Ultralytics.
