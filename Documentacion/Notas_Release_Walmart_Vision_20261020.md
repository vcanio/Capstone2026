# Walmart Visión · V1 y V2

Walmart Lite pasa a llamarse **Walmart Visión**. Esta entrega permite probar fotografías propias con los cuatro modelos conservados y revisar sus predicciones en un visor local.

## Cambios

- **0. Seleccionar versión** organiza el inicio: V1 o V2 determina los modelos y estados disponibles.
- **Original, Niveles, Bordes y Comparar** reúnen las imágenes en el visor principal. El mapa de señal está en Bordes, con opciones para mostrar los bordes de la foto o de los niveles.
- Comparar muestra la fotografía y la predicción juntas. Los resúmenes identifican el modelo que produjo el resultado.
- Cambiar foto, versión, modelo, método o confianza descarta la predicción anterior y permite analizar de nuevo.
- Nombre, iniciador de Windows, instrucciones y cuaderno de Colab actualizados a Walmart Visión. Colab también permite elegir versión y revisar las cuatro vistas.

## Descargar y usar

Descargar **Walmart_Vision_20261020.zip**, extraerlo por completo y abrir **Walmart_Vision/iniciar.cmd**. La primera ejecución requiere Internet y prepara Python 3.12 y las dependencias dentro de la carpeta. Los siguientes arranques reutilizan ese entorno. Windows x64, CPU; no requiere CVAT, Docker ni Python instalado previamente.

El ZIP incluye **YOLO11-1, YOLO26-1, V2-YOLO11 y V2-YOLO26**, sus hashes, el visor y **Probar_en_Colab.ipynb**. Se conservaron los pesos entrenados; esta actualización no vuelve a entrenar los modelos. Los archivos automáticos «Source code» de GitHub no contienen los pesos: para probar la aplicación hay que descargar el ZIP indicado.

V1 distingue vacío, baja disponibilidad, suficiente y no evaluable. V2 base distingue reponer y suficiente; no reconoce no evaluable. Bordes, color y textura aportan señal experimental y no modifican el estado de YOLO ni miden un porcentaje validado de producto. Una foto propia sin anotaciones permite revisar predicciones, pero no calcular precisión.

Las fotos locales se procesan en memoria y no se guardan ni se usan para entrenar. Colab procesa los archivos que se suban en el entorno de Google. La descarga pública incluye solo la aplicación; los conjuntos de desarrollo, la reserva y los informes se distribuyen por separado.

## Verificación

43 pruebas automatizadas: aplicación e interfaz (20), bordes (13) y preparador del laboratorio (10). Comprobación de los cuatro modelos en CPU, con ambos métodos, y de que los bordes conservan estados y confianzas de YOLO. Revisión del visor en escritorio y móvil. Se comprueban la integridad del ZIP, los hashes de pesos y código de bordes y la sintaxis del cuaderno.

No se ejecutó el cuaderno en una sesión real de Colab ni se probó esta entrega en otro computador físico.

SHA-256 de `Walmart_Vision_20261020.zip`: `4ca1002d3d4f920987f47d7696c67ff6c247c5036f879ed2efd6e690335947e2`.
