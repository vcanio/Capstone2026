# Walmart Lite V2 y laboratorio reproducible - avance intermedio

Versión `avance-2026-10-20`. Prototipo académico en evaluación; quedan pendientes
la instalación en otro computador físico y la ampliación de la validación real.

## Para probar fotografías: Walmart Lite

Descargar el activo **Walmart_Lite_V2_20261020.zip** (aproximadamente 36 MiB),
extraer todo y abrir **Walmart_Lite/iniciar.cmd** en Windows x64. Mantener la
consola abierta mientras se utiliza la aplicación. El visor se abre en
http://127.0.0.1:8095.

- Incluye YOLO11-1, YOLO26-1, V2-YOLO11 y V2-YOLO26.
- Permite cargar fotos JPG, PNG o WebP y revisar niveles, estados y alertas.
- No requiere instalar previamente Python, Docker o CVAT.
- El primer inicio necesita Internet y espacio para descargar Python y sus
  dependencias; las siguientes ejecuciones reutilizan el entorno local.
- Las fotos se procesan localmente en CPU, no se guardan ni se añaden a entrenamiento.

**Descargar el ZIP con el nombre anterior en Assets.** Los archivos automáticos
“Source code (zip)” y “Source code (tar.gz)” contienen el código del repositorio,
pero no son el paquete portátil con los pesos incluidos.

## Para desarrollar o replicar: laboratorio completo

Clonar el repositorio y ejecutar el preparador como indica el
[README de esta versión](https://github.com/vcanio/Capstone2026/blob/avance-2026-10-20/README.md).
Los otros activos proporcionan imágenes, exportaciones congeladas, pesos,
resultados y el informe intermedio. artefactos.json y SHA256SUMS.txt fijan su
integridad. El inicio base del panel usa CPU y no necesita credenciales de CVAT.

El panel completo incluye **YOLO + bordes de Paulo, revisión 2**, que combina
bordes, color y textura dentro de los niveles localizados por YOLO. Incluye
mapas de señal, vistas de bordes y las comparaciones conservadas. Esta función
experimental todavía no forma parte de Walmart Lite.

## Límites que deben conocerse

- V1 reconoce vacío, baja disponibilidad, suficiente y no evaluable. V2 base
  reconoce reponer y suficiente; todavía no reconoce no evaluable.
- La confianza de YOLO y la señal de bordes no son un porcentaje real de ocupación.
  El análisis de Paulo conserva el estado asignado por YOLO.
- La validación V2 tiene diez fotografías reales y un solo nivel reponer;
  las métricas no demuestran generalización a otros locales o condiciones.
- El informe intermedio registra veinte casos y el alcance de su corte; la
  revisión de bordes está documentada por separado en el repositorio.

Se comprobó la instalación desde activos locales, el panel Docker en CPU y la
demo extraída del ZIP. Con V2-YOLO26, la imagen de ejemplo
lider_express_040_0_original.jpg produjo cinco niveles: cuatro suficientes y uno
reponer. Es una prueba de funcionamiento, no una medida de precisión global.

Las instrucciones para colaborar con ramas, PR y pull están en
[Trabajo en equipo](https://github.com/vcanio/Capstone2026/blob/avance-2026-10-20/Documentacion/Trabajo_en_equipo.md).
