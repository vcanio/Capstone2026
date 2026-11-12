# Conservación de contornos de productos · 8 de noviembre

Vicente reportó que la vista de bordes dentro de los niveles perdía los lados de los envases. El preprocesamiento V2 aplicaba `quitar_lineas_largas()` después de excluir rieles. Esa función borra rectas en cualquier orientación: en una comprobación sintética eliminaba los 400 píxeles del contorno rectangular de un envase.

## Corrección

En `Aplicacion/ocupacion_paulo.py`, V2/Línea A conserva Canny y aplica únicamente la máscara estructural ya calculada por `_exclude_structure()`. Se mantienen el margen interior, la detección de rieles horizontales extensos, las barandas inferiores fragmentadas y el límite de exclusión del 20 % de la región. V1 conserva su ruta de compatibilidad. Las rectas locales y los lados verticales de los productos ya no se borran por su longitud. El filtro estructural sigue siendo heurístico, no un clasificador semántico de envases.

La corrección afecta tanto al diagnóstico de bordes como a la densidad usada por Línea A. No se cambia su umbral 52 ni el núcleo decisor. `Bordes filtrados dentro de los niveles` aclara el nombre de la vista. La revisión `linea_a_20261108_contornos_conservados` viaja en API y catálogo; invalida resultados guardados de revisiones previas al recuperar la sesión, conservando fotos y marcas. Los hashes del manifiesto se actualizan.

## Verificación

- 90 ejecuciones de pruebas de aplicación correctas, incluidas dos nuevas regresiones: conservación de lados/tapa de envase y exclusión de baranda con producto por encima.
- 11 pruebas de Línea A/sandbox correctas y `app.py --check` correcto.
- Recalculados los 164 niveles etiquetados de desarrollo con máscaras humanas. Línea A conserva en los 112 de validación: 15 TP, 0 FP, 1 falso suficiente y 0 revisiones; F1 96,77 %. En reales: 1/2 positivos detectados; en sintéticas: 14/14. El falso suficiente sigue siendo R240, nivel 3. Las puntuaciones individuales cambian; no se recalibró el umbral ni se sobrescribió la comparación histórica. La columna del estimador antiguo, recalculada con el preprocesamiento corregido, ya no equivale a su referencia histórica congelada.
- En `lider_express_014_A_vacios.png`, usando las mismas máscaras humanas, los bordes conservados pasan de 36.757 a 67.995 píxeles: 31.238 recuperados. Se inspeccionó la comparación visual. No se afirma que todos los píxeles recuperados sean producto ni que todas las estructuras queden eliminadas.
- Dos inferencias HTTP en CPU desde ZIP aislado: `014_A_vacios` detecta seis niveles, con 1 y 4 Reponer; `020_A_vacios` detecta cinco, con 2 y 4 Reponer. El resultado devuelve la revisión corregida y sus mapas.

Evidencia en `.tmp/correccion_contornos_20261108/`: `evaluacion_mascaras_humanas.json`, `comparacion_bordes.json`, `comparacion_bordes.png` y `verificacion_http.json`. La comprobación usa desarrollo; test final, pesos, CVAT y particiones se conservan. Actualización local, sin modificar las releases publicadas.
