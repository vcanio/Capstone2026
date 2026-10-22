# Detección de bordes V2 · combinación ponderada

La V2 integra `gondola_combinacion_ponderada.py`, aportado por Paulo, en el panel de desarrollo y en Walmart Visión. La detección anterior se conserva como **Bordes V1 · color y textura**; su identificador histórico sigue siendo `paulo_mascara_v2_color_textura`.

Para probarla, selecciona **Método de análisis → YOLO + bordes V2 → Analizar foto**. En el panel de desarrollo, este selector aparece al usar un modelo de niveles V2. La versión de bordes se elige por separado de la versión del modelo YOLO.

La nueva señal usa bordes (35 %), gradiente (30 %), color (20 %) y textura (15 %), normalizados mediante los percentiles 10 y 90 de cada nivel. El umbral Otsu queda limitado al intervalo 0,35–0,62. La apertura está desactivada por defecto y se aplica cierre de 3 × 3 celdas.

El resultado combina **70 % de superficie + 30 % de cobertura horizontal**. Una columna se considera cubierta cuando al menos el 20 % de sus celdas utilizables supera el umbral, antes del cierre morfológico. Walmart Visión muestra ese combinado como **ocupación estimada por nivel**, rojo bajo el 30 % y verde desde el 30 %. El desglose de **Combinado**, **Área con señal** y **Ancho con señal** queda en los detalles; el panel de desarrollo conserva las tres mediciones.

La adaptación al visor conserva la política de máscaras existente: calcula sobre los píxeles originales, limita las celdas y la normalización a la máscara raster de YOLO, aplica un margen interior y reduce el lado máximo a 1600 píxeles. No sustituye la máscara por la caja rectangular del script independiente. Los niveles pequeños, las máscaras ausentes y los estados no evaluables conservan el resultado **Sin medición**.

Los resultados registran `paulo_mascara_v2_combinacion_ponderada`, los parámetros y los hashes de las fuentes. En la API del visor se selecciona con `method=yolo_paulo_v2`; en los trabajos del panel, con `occupancy=true` y `occupancy_version="v2"`. Los trabajos antiguos mantienen V1 por defecto y no se recalculan automáticamente.

Los porcentajes son señales experimentales, sin calibración de ocupación real. La combinación no modifica clases, confianza ni alertas de YOLO. El empaquetador incluye ambos scripts y verifica sus hashes; para distribuir esta mejora hay que generar un paquete nuevo.
