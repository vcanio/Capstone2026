# Verificación de Walmart Lite — 15 de octubre de 2026

> **Registro histórico · Lite V1 con dos modelos.** Estas comprobaciones corresponden al paquete inicial. La entrega actual utiliza cuatro modelos y se documenta en [Verificación de Walmart Visión](VERIFICACION_VISION.md). Para instalarla, seguir [Usar Walmart Visión](../../Documentacion/Usar_Walmart_Vision.md). Véase el [índice histórico](../../Documentacion/Historico/README.md).

El paquete fue extraído en una carpeta separada y ejecutado con solo sus archivos y pesos, sin montar datos, CVAT, anotaciones, credenciales ni el resto del proyecto.

## Comprobado

- Integridad ZIP y coincidencia SHA-256 de ambos pesos con los `best.pt` originales.
- Diez pruebas automatizadas de carga, orientación EXIF, transparencia, formatos y tamaños, pesos alterados, modelos desconocidos, confianza inválida, concurrencia, respuestas HTTP, protección de rutas/orígenes y preparación del entorno.
- Sintaxis de Python, JavaScript y todas las celdas Python del cuaderno. El cuaderno incluye IDs de celda y está sin resultados ni archivos del usuario.
- Predicciones reales en **CPU** con YOLO11-1 y YOLO26-1, mediante la API del paquete extraído. Ambos devolvieron la imagen anotada y sus recuentos sin usar el proyecto original.
- Prueba de interfaz con carga de una foto de desarrollo, selección de modelo y ejecución real. La imagen usada fue una copia reducida de REAL_15; no constituye una evaluación independiente de precisión.
- Revisión visual en escritorio y móvil, sin desbordamiento horizontal; resultado, recuentos, alternancia de vista y enlace de descarga disponibles.
- Etiquetas renovadas: cápsula blanca, número separado con fondo suave según el estado y tipografía más compacta. Se comprobaron las cuatro clases a 363 px de ancho, una predicción real nueva con YOLO26-1 en el panel y las diez pruebas de la demo. Las predicciones históricas conservan su aspecto anterior.

La interfaz se comprobó inicialmente con Python 3.11, PyTorch 2.5.1 y Ultralytics 8.4.174 en un contenedor aislado sin GPU. **Docker no forma parte de los requisitos del paquete**. El programa distribuido abre su servidor en 127.0.0.1; el contenedor de prueba tuvo una adaptación de red limitada a localhost para inspeccionarlo desde el navegador.

## Preparación automática en Windows

Se extrajo el paquete en una carpeta nueva con espacios en su nombre y se ejecutó `iniciar.cmd --verificar` en este Windows x64, que ya tenía **Python 3.13.5**. Este modo ejecuta la preparación real sin abrir el navegador ni dejar el servidor iniciado.

- El iniciador descargó automáticamente **CPython 3.12.15** dentro de `.runtime/python`, creó `.entorno-py312` e instaló PyTorch 2.5.1+cpu, torchvision 0.20.1+cpu y las dependencias fijadas.
- La comprobación terminó correctamente con ambos pesos. Después se analizaron fotos con **YOLO11-1 y YOLO26-1 en CPU** usando ese entorno privado.
- Se comprobó el servidor HTTP real en Windows: página, lista de modelos y carga de una foto con imagen anotada y recuentos devueltos por la API.
- Un segundo arranque con `UV_OFFLINE=true` reutilizó el entorno listo, sin descargar ni instalar paquetes. `python --version` siguió devolviendo **3.13.5**.
- El código dirige la configuración de Ultralytics y Matplotlib a `.runtime/config` dentro del paquete. El preparador no instala Python globalmente ni registra sus ejecutables en Windows.

Los dos modelos detectaron seis niveles en la foto de desarrollo usada: un vacío, uno de baja disponibilidad y cuatro suficientes. Esta observación comprueba el funcionamiento de la entrega; no mide precisión ni sustituye una validación independiente.

## Alcance de la comprobación

La preparación automática se ejecutó desde cero en una carpeta separada de este Windows; todavía no se ha probado en otro PC físico. El primer inicio requiere Internet, Windows x64 compatible y permisos para escribir en la carpeta. No requiere Python previamente instalado. Los siguientes inicios y predicciones pueden funcionar sin conexión.

El cuaderno está preparado para Colab y su código fue comprobado estáticamente; **no se ejecutó en una sesión real de Colab**. La disponibilidad de recursos y futuras versiones del entorno de Colab se comprueban al abrirlo allí. El mismo módulo de inferencia sí se ejecutó con ambos pesos en el entorno aislado local.

Los modelos, etiquetas, particiones y resultados históricos del proyecto no se modificaron. Este ZIP contiene inferencia y no incluye entrenamiento, CVAT, imágenes de desarrollo, configuraciones privadas ni la reserva final.
