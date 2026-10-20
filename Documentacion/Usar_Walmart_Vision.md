# Usar Walmart Visión

Walmart Visión permite cargar una fotografía de una góndola, localizar sus niveles y revisar el estado que predice un modelo ya entrenado. Esta es la aplicación destinada al usuario. El panel de entrenamiento y CVAT son herramientas del equipo de desarrollo; no se necesitan para este recorrido.

## Requisitos y descarga

- Un computador con Windows x64 y una carpeta local con permiso de escritura.
- Internet durante el primer inicio para descargar Python y las dependencias. Los siguientes arranques reutilizan el entorno instalado y permiten analizar fotos localmente sin conexión.
- Una fotografía propia en JPG, PNG o WebP, sin animación, de hasta 15 MB y 24 megapíxeles.

Descargar **Walmart_Vision_20261020.zip** desde la [Release de Walmart Visión](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-2026-10-20). Los archivos automáticos «Source code» contienen el código del repositorio; el ZIP de Visión incluye los cuatro modelos necesarios para usar la aplicación.

El iniciador prepara Python 3.12 y las bibliotecas dentro de la carpeta de la aplicación. No hace falta instalar previamente Python, Docker, CVAT ni disponer de una GPU NVIDIA. El análisis utiliza CPU; su duración depende del computador. La instalación ocupa más espacio que el ZIP descargado por sus dependencias.

## Iniciar y analizar una fotografía

1. Extraer **todo** el ZIP. No ejecutar la aplicación desde dentro del archivo comprimido.
2. Abrir `Walmart_Vision/iniciar.cmd` y mantener la consola abierta. El primer inicio puede tardar varios minutos mientras prepara las dependencias.
3. Esperar a que abra el navegador en http://127.0.0.1:8095. Si no se abre automáticamente, entrar a esa dirección.
4. En **0. Seleccionar versión**, elegir V1 o V2 y seleccionar un modelo.
5. Cargar o arrastrar una foto, elegir **Solo YOLO** o **YOLO + detección de bordes** y pulsar **Analizar foto**.
6. Revisar **Original**, **Niveles** y **Comparar**. Con el método de bordes también se habilita **Bordes**, con el mapa de señal y las vistas de contornos.

Cambiar foto, versión, modelo, método o confianza descarta la predicción anterior y requiere analizar de nuevo. Para terminar, pulsar Ctrl+C en la consola.

## Interpretar los resultados

| Resultado | Qué significa |
|---|---|
| Región o máscara sobre una repisa | El modelo localizó un nivel y dibujó su contorno. |
| V1: vacío o baja disponibilidad | Señala una posible necesidad de reposición. También distingue suficiente y no evaluable. |
| V2 base: reponer o suficiente | Son sus dos estados disponibles. No reconoce no evaluable; hay que revisar especialmente las fotos con obstáculos. |
| Confianza | Puntuación de la predicción; no representa el porcentaje de productos en la repisa. |
| Señal de bordes, color y textura | Análisis experimental dentro de las máscaras. No cambia el estado YOLO ni mide un porcentaje validado de ocupación. |

Una predicción puede omitir un nivel, dibujarlo mal o asignarle un estado incorrecto. Revisar visualmente el resultado antes de usarlo como apoyo para decidir. La aplicación no cuenta SKU ni consulta inventario de bodega. Una foto propia sin anotaciones de referencia permite observar predicciones, pero no calcular precisión.

Las fotografías se procesan en memoria en el computador: no se guardan ni se usan para entrenar. El ZIP no incluye las imágenes del dataset. El cuaderno opcional de Colab tiene un recorrido distinto y sube los archivos seleccionados al entorno de Google; sus instrucciones están en la [guía incluida en la aplicación](../Herramientas/Demo_lite/LEEME.md#colab).

## Si no inicia

| Situación | Acción |
|---|---|
| Falló la descarga inicial | Revisar la conexión y volver a abrir `iniciar.cmd`. El registro queda en `.runtime/instalacion.log`, dentro de la carpeta de Visión. |
| El puerto 8095 está ocupado | Cerrar otra instancia o abrir una consola en la carpeta de Visión y ejecutar `iniciar.cmd --port 8096`; entrar a http://127.0.0.1:8096. |
| No aparecen los modelos o falla su integridad | Extraer nuevamente el ZIP completo en otra carpeta y conservar el mensaje de error si se repite. |
| La foto no se acepta | Comprobar formato, tamaño y dimensiones según los requisitos anteriores. |
| La primera predicción tarda | Esperar a que se carguen los pesos y revisar la consola; el tiempo depende de la CPU. |

## Comprobar la instalación en otro computador

**Estado: pendiente.** Se verificaron la interfaz y la inferencia CPU desde un ZIP extraído en el equipo de desarrollo. Eso no acredita una instalación en otro computador físico. El [registro de verificación de Visión](../Herramientas/Demo_lite/VERIFICACION_VISION.md) conserva el alcance de las pruebas ya realizadas.

Para cerrar esta comprobación, una persona debe seguir los pasos anteriores en otro computador físico, usando el ZIP descargado desde la Release y sin copiar el entorno Python preparado del equipo de desarrollo:

1. Registrar fecha, persona que prueba, versión de Windows, CPU, RAM y nombre del ZIP. Comparar su SHA-256 con el de las [notas de la versión](Notas_Release_Walmart_Vision_20261020.md), por ejemplo con `Get-FileHash -Algorithm SHA256 .\Walmart_Vision_20261020.zip` en PowerShell.
2. Extraer el ZIP e iniciar con Internet para comprobar la preparación automática y la apertura del visor.
3. Analizar una fotografía propia autorizada con cada uno de los cuatro modelos, probando **Solo YOLO** y **YOLO + detección de bordes**. Registrar si cada combinación termina y muestra su resultado, incluso si no detecta niveles.
4. Revisar las cuatro vistas cuando correspondan, cambiar la foto y comprobar que se limpia el resultado anterior.
5. Cerrar y volver a abrir la aplicación con el entorno ya preparado y sin conexión; analizar otra vez para comprobar el uso local.
6. Registrar incidencias y adjuntar capturas autorizadas o mensajes de error. Completar el registro de verificación solo con lo que realmente se ejecutó.

Plantilla para registrar el resultado:

| Campo | Registro por completar |
|---|---|
| Fecha y persona | Pendiente |
| Windows, CPU y RAM | Pendiente |
| Nombre y SHA-256 del ZIP | Pendiente |
| Preparación inicial y apertura | Pendiente |
| Cuatro modelos con ambos métodos | Pendiente |
| Vistas y cambio de foto | Pendiente |
| Reinicio e inferencia sin conexión | Pendiente |
| Incidencias y evidencias | Pendiente |
| Resultado de la instalación: correcta o con incidencias | Pendiente |

Esta comprobación acredita el recorrido de instalación y uso en ese equipo. La precisión de los modelos requiere una evaluación con referencias y conserva las limitaciones documentadas.

## Entender cómo se construyó

La [guía conceptual](Guia_para_entender_el_proyecto.md#cómo-se-relacionan-las-tres-interfaces) explica la anotación, el entrenamiento y la aplicación de usuario. La [arquitectura y el mapa del código](Evolucion_v1_v2.md) permiten ubicar su implementación. Para continuar el desarrollo, consultar la [guía técnica del laboratorio](Replicar_proyecto.md), que requiere activos gestionados por el equipo.
