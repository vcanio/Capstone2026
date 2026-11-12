# Metodología de desarrollo y revisión

El desarrollo de Walmart Visión combinó anotación en CVAT, un laboratorio interno para seguir los ensayos y una aplicación de revisión del equipo para inspeccionar las predicciones. La app cliente es el producto principal que se entrega; la app del equipo apoya su revisión. El laboratorio se conserva como herramienta interna y evidencia técnica del proceso.

## 1. Anotación de los niveles en CVAT

El equipo utilizó **CVAT para marcar y revisar los niveles de las góndolas mediante polígonos de la clase `Nivel`**. Cada polígono delimita el área útil de una repisa del mismo tramo, incluidos productos y huecos; no representa una máscara por producto ni una etiqueta de stock.

Se aplicó un criterio común: apoyo sobre el portaprecio, exclusión de su franja y respeto del techo físico cuando existe. En superiores abiertos se utilizó la mediana de las alturas inferiores cuando correspondía, con las excepciones y recortes documentados. Los atributos de delimitación y oclusión registran información de la anotación; no son clases que el modelo prediga.

Las anotaciones pertenecen al equipo, según lo confirmado por Vicente. Se conservaron las revisiones y los registros de correcciones geométricas asistidas. Esta descripción no convierte una preanotación o una predicción sin revisión en una etiqueta humana aprobada. [Criterio de niveles](Desarrollo/Criterio_V3_niveles.md) · [Regla de superiores](Desarrollo/Regla_nivel_superior_mediana_V3.md) · [Autoría y condiciones](../LICENCIAS.md).

## 2. Preparación y seguimiento en el laboratorio interno

Se construyó un laboratorio con interfaz visual para organizar la preparación de datos, configurar los ensayos y consultar métricas, curvas por época, resultados y decisiones sobre los modelos. Esto permitió seguir el progreso de los experimentos y conservar sus parámetros y referencias.

El código de preparación, entrenamiento y evaluación se mantiene en GitHub para facilitar la revisión técnica y la continuidad del proyecto. La interfaz del laboratorio es una ayuda de desarrollo: no se requiere para usar las apps y no forma parte del ZIP cliente/equipo. El clon público tampoco incluye los activos privados necesarios para repetir todos los ensayos.

El localizador está cerrado de momento con el peso adoptado el 10/11. Un futuro refuerzo requiere un plan nuevo; **solo Vicente inicia entrenamiento desde el panel**. Consultar curvas o preparar archivos no inicia un entrenamiento. [Laboratorio interno](../Laboratorio/README.md) · [Entrenamiento documentado](Desarrollo/Entrenamiento_geometrico_V3.md).

## 3. Revisión visual en la app del equipo

Las predicciones se inspeccionaron mediante la aplicación de revisión del equipo, comparando la fotografía con los contornos y mapas de señal. Sus herramientas permiten registrar niveles omitidos, detecciones adicionales y contornos incorrectos por foto, nivel o zona, y exportar lotes de revisión.

Estas observaciones no modifican automáticamente CVAT, los pesos o los datos de entrenamiento. La revisión visual humana complementa las métricas cuantitativas, pero **no equivale a mAP, recall ni exactitud de ocupación**. Las métricas se informan con su partición y condiciones de evaluación. [Guía de revisión](../Aplicacion/Documentacion/REVISION_EQUIPO.md) · [Modelo, resultados y límites](Modelo_V3_actual.md).

## 4. Entrega de las aplicaciones

El cliente presenta alertas visuales, revisión humana y CSV. La app del equipo aporta los controles de inspección y los lotes de revisión. Ambas comparten el modelo oficial y el motor de ocupación Línea A. Para utilizarlas no se necesita CVAT ni el laboratorio.

Las fotos cargadas y las marcas guardadas en las apps no se incorporan automáticamente al entrenamiento. El índice de ocupación sigue siendo preliminar; las pruebas funcionales y la inspección visual no constituyen una evaluación final del sistema. [Descarga de las apps](../Entregables/README.md) · [Funcionamiento](Guia_para_entender_el_proyecto.md).
