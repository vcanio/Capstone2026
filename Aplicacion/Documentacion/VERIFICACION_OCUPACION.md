> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../Modelos/Actual/README.md).

# Vista simplificada de ocupación · 22 de octubre de 2026

La vista con bordes muestra un porcentaje de ocupación estimada por nivel. Usa el combinado de V2 (70 % de área y 30 % de ancho) o el área con señal de V1. Rojo indica menos del 30 % y verde, 30 % o más. Sin medición se comunica en gris. La imagen, la tabla, Comparar y la descarga usan la misma lectura. Los estados originales de YOLO siguen disponibles en su detalle.

Se ejecutaron 27 pruebas de la aplicación: límite 29,99/30 %, cero, cien, datos ausentes o inválidos, colores de la imagen, estados originales, reinicio al cambiar parámetros, interfaz y rutas HTTP. Todas pasaron. Se ejecutaron fuera del sandbox porque los sockets locales y las carpetas temporales de las pruebas estaban restringidos.

Se probó la interfaz real con V2-YOLO26 y bordes V2 en CPU. El caso B09 del archivo de evidencias produjo seis niveles: dos rojos (16,51 % y 11,91 %) y cuatro verdes. B09 es una variante sintética del material de diagnóstico, no una nueva fotografía de validación independiente. También se ejecutó F10, con seis lecturas verdes. Estos ejemplos comprueban el recorrido y la presentación; no validan la exactitud de la estimación.

Se revisaron capturas de escritorio y móvil de 390 px, en temas claro y oscuro. En móvil el ancho del documento coincidió con el ancho del visor, sin desbordamiento horizontal. Las capturas se conservan en `Documentacion/Evidencias/vision_ocupacion_20261022/` del proyecto fuente. El detector de diseño señaló tres imágenes inicialmente sin `src`: son los visores ocultos que la aplicación completa al cargar una foto o mostrar una comparación; no se mostraron imágenes rotas en la revisión.

El porcentaje sigue siendo experimental y pendiente de calibración. El umbral del 30 % es una regla de presentación solicitada para esta versión, no una validación de la regla de reposición sobre ocupación real. No se han vuelto a entrenar los modelos. La publicación se comprueba por separado en GitHub. Los ZIP anteriores conservan su contenido. La revisión en este equipo no acredita instalación en otro computador ni prueba física en Mac.
