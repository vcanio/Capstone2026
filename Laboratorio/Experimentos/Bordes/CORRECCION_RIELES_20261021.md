# Corrección de rieles en la señal de ocupación

El caso `lider_express_055_C_mixta.png` mostraba una barrera sin bordes visibles en el mapa Canny filtrado, pero activada en amarillo. La desviación de brillo de la barrera seguía superando el umbral de textura: quitar líneas del mapa de bordes no quitaba sus píxeles de las demás características.

La integración compartida por Bordes V1 y V2 ahora detecta bandas horizontales largas con un Canny auxiliar sensible a estructuras tenues. Exige al menos el 45 % del ancho del nivel, pendiente máxima de 0,12 y una banda fina de aproximadamente media celda. Si las bandas cubren más del 20 % de los píxeles del nivel, descarta esa exclusión para evitar borrar tramas densas de productos.

La misma exclusión se aplica a bordes, color, momentos de brillo, gradiente y a la reproyección final del mapa amarillo. Los momentos se normalizan por los píxeles observados sin riel, conservando como denominador de ocupación la superficie original de la máscara. El cierre de la grilla no puede volver a pintar los píxeles excluidos. Los resultados registran `structure_policy: rieles_horizontales_v1` y nuevos hashes de código; los análisis guardados anteriormente no cambian.

Se congelaron las cinco máscaras YOLO del caso recibido y se aplicaron ambas revisiones sobre los mismos píxeles. En el recorte de barrera sin productos `(420, 592)–(800, 635)`, la fracción de píxeles pintados por V1 pasó de 90,7 % a 0 %. V2 ya daba 0 % en ese recorte y conserva ese valor. En el interior de las tres botellas del cuarto nivel, V2 conserva señal en el 95,62 % del recorte de comprobación. Estas fracciones describen regiones de regresión; no son referencias de ocupación real.

Las pruebas cubren rieles tenues sin productos, productos con bordes verticales y color, texturas densas, máscaras, ausencia de medición y la fórmula ponderada. Se conserva la clasificación YOLO existente durante esta corrección.

## Dirección acordada para el sistema

El flujo previsto es **YOLO delimita el nivel → visión clásica estima ocupación → una regla de negocio decide reposición**. La clase `reponer` que hoy predice YOLO deja de ser la decisión final en esa arquitectura. La localización debe admitir niveles independientemente de su estado, mediante entrenamiento de una clase geométrica `Nivel` o una adaptación explícita del modelo existente.

Antes de activar esa decisión hay que fijar qué se mide: superficie visible, cobertura horizontal o una combinación. El 30 % usado en las anotaciones originales corresponde al ancho; no se puede trasladar directamente a una combinación de área y ancho. Se necesitan mediciones de referencia para calibrar y evaluar la regla, con estados separados para regiones no evaluables. Los porcentajes actuales siguen siendo señales experimentales.

La corrección de rieles no valida la ocupación global. Queda pendiente estudiar, entre otros casos, la normalización por percentiles en niveles con productos muy dispersos y los fondos con textura.
