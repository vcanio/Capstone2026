> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../Modelos/Actual/README.md).

# Revision documental del paquete del 23/10/2026

El ZIP local del 23/10 conserva pesos, inferencia e interfaz. Se corrigieron instrucciones y fecha del manifiesto para identificar los dos modelos V2. El empaquetador comprueba integridad ZIP y hashes de pesos. Las comprobaciones de CPU, interfaz y plataformas que siguen pertenecen a la revision anterior: este empaquetado no las convierte en una nueva evaluacion ni en una prueba de Mac o Colab.

## Comprobaciones anteriores conservadas

# Walmart Visión: solo la versión actual

El visor abre directamente en «Prueba tu foto». Se retiraron la pantalla de selección de versiones, el cambio de versión y sus estilos y eventos. El paquete incluye únicamente V2-YOLO11 y V2-YOLO26, con V2-YOLO26 como modelo inicial indicado en el manifiesto. El selector de modelo permite comparar las dos arquitecturas de la misma versión. Los métodos visibles son YOLO con bordes ponderados y Solo YOLO. Colab conserva el mismo criterio y no ofrece versiones anteriores.

Se ejecutaron 28 pruebas de la aplicación: todas pasaron. Incluyen estados, limpieza de resultados al cambiar parámetros, vistas, teclado, tema, imagen, límites, integridad y rutas HTTP. Las pruebas se ejecutaron fuera del sandbox por sus restricciones sobre sockets locales y temporales.

Se extrajo el ZIP y se ejecutó inferencia CPU con ambos modelos y ambos métodos sobre B09, una variante sintética de diagnóstico. Las cuatro combinaciones devolvieron seis niveles y conservaron los dos estados V2. También se comprobó que la llamada sin modelo usa el predeterminado del manifiesto. Se verificaron integridad del ZIP, hashes de pesos y módulos de bordes, ausencia de pesos V1 y sintaxis de las celdas de Colab. No se ejecutó una sesión remota de Colab.

Se revisó la interfaz real en escritorio y móvil de 390 px. El visor abre directamente, muestra solo los dos modelos V2 y no contiene controles de versión. El ancho del documento coincidió con el área disponible en móvil. El detector señaló los tres elementos de imagen que se mantienen ocultos hasta tener foto o resultado; no aparecieron imágenes rotas en la pantalla revisada.

Las capturas, el resultado de ambos modelos y el registro con tamaño y SHA-256 del paquete están en `Documentacion/Evidencias/vision_actual_20261022/` del proyecto fuente. La revisión visual se terminó el 23 de octubre de 2026.

Las versiones anteriores se conservan en sus Releases. Este paquete está preparado localmente; no se publicó una nueva Release. La estimación de ocupación sigue siendo experimental. Estas comprobaciones no acreditan precisión, instalación en otro computador físico ni una nueva construcción Docker en macOS.
