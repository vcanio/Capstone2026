# Metodología de desarrollo y revisión

Walmart Visión se desarrolló mediante ciclos de captura, anotación, entrenamiento, inspección y ajuste. El equipo mantuvo dos reuniones semanales para revisar avances y acordar el siguiente trabajo. Se aplicaron prácticas ágiles de inspección y adaptación, sin atribuir roles, sprints o una implantación formal completa de Scrum.

## Anotación del dataset propio con CVAT

El equipo utilizó **CVAT para marcar y revisar polígonos de la clase Nivel**. Cada región incluye el área útil de una repisa, productos y huecos; no representa una máscara por producto ni una etiqueta de stock. La base se sitúa sobre el portaprecio y el superior abierto sigue la mediana de las alturas inferiores cuando corresponde. Los atributos de delimitación y oclusión registran revisión; no son clases predichas por el modelo. [Criterio completo](Criterio_de_niveles.md).

Se conservaron las revisiones manuales y las correcciones geométricas asistidas. Una preanotación o predicción no se considera etiqueta humana aprobada por sí sola. La autoría de las capturas y anotaciones fue confirmada por Vicente; ello no concede una licencia pública al dataset ni acredita permisos institucionales adicionales. Las variantes sintéticas se identifican como tales. [Licencias y procedencia](../LICENCIAS.md).

## Laboratorio y GPU local

Se construyó un laboratorio interno para preparar exportaciones, configurar ensayos y consultar métricas, curvas por época y resultados. Se utilizó la GPU propia para entrenar sin depender de sesiones de Google Colab. Este fue un medio de desarrollo del modelo, no una función requerida por el cliente.

Las imágenes y variantes relacionadas se agruparon por escena/familia; no se repartieron al azar para aparentar independencia. Las selecciones, exclusiones y exportaciones se registraron con hashes. Los datos reales y sintéticos se informaron por separado. La cadena V3, el último ensayo y los límites de comparación están en [Entrenamiento y datos](Entrenamiento_y_datos.md).

El localizador quedó cerrado de momento con el peso adoptado el 10/11. Un futuro refuerzo requiere un plan nuevo desde ese oficial; **solo Vicente inicia entrenamiento desde el panel local**. No usar test para inferencia, selección o ajustes. R254 permanece excluida. La retirada de herramientas de main no autoriza nuevos ensayos ni modifica el entorno local.

## Revisión visual con la app del equipo

La app del equipo permite comparar la fotografía con contornos y mapas de señal, registrar niveles omitidos, detecciones adicionales y contornos incorrectos por nivel o zona, y exportar lotes de revisión. Sus observaciones no modifican automáticamente CVAT, los pesos ni el entrenamiento.

Esta revisión complementa las métricas cuantitativas, pero **no equivale por sí sola a mAP, recall o exactitud de ocupación**. El lote de **Ohiggins 3** (68 fotos) quedó posteriormente anotado en CVAT y evaluado en frío de forma cuantitativa el 14/11/2026 ([Evidencia de test](Evidencias/evaluacion_test_ohiggins3_20261114.md)), manteniéndose fuera de `train` para evitar fugas. [Modelo y resultados](Modelo_V3_actual.md) · [Guía de revisión](../Aplicacion/Documentacion/REVISION_EQUIPO.md).

## Producto y trabajo de ocupación

La app cliente presenta alertas visuales, revisión humana y CSV. La app del equipo aporta comparación, diagnóstico y lotes de revisión. Ambas comparten el peso oficial y Línea A; no necesitan CVAT ni el laboratorio. Las fotos cargadas no se incorporan automáticamente al entrenamiento.

Localización de niveles y estimación de ocupación son evaluaciones distintas. El índice 0–100 y umbral 52 son preliminares y no miden stock físico. Las limitaciones reales y las pruebas funcionales se conservan sin presentarlas como evaluación final. Las herramientas internas y antecedentes pueden consultarse en [Archivo del desarrollo](Archivo_del_desarrollo.md).
