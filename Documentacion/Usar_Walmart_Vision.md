# Usar Walmart Visión V3

Las apps del 11/11 comparten el cierre V3 revisado adoptado el 10/11 y Línea A del 8/11. [Descarga vigente e historial](../Entregables/README.md). El cliente muestra alertas visuales, revisión humana y CSV; la mesa del equipo añade controles técnicos y lotes de revisión.

## Abrir

En Windows, abre [iniciar_cliente.cmd](../Aplicacion_Cliente/iniciar_cliente.cmd) para el cliente (8098) o [Aplicacion/iniciar.cmd](../Aplicacion/iniciar.cmd) para el equipo (8095). En el ZIP conjunto, los iniciadores están en la raíz. En Docker, ejecuta `docker compose -f compose.apps.yaml up --build -d --wait` desde la raíz y abre http://127.0.0.1:8098 o http://127.0.0.1:8095. La primera instalación requiere Internet; no necesitas el laboratorio ni CVAT para analizar fotos.

## Cliente: alertas y revisión humana

El recorrido muestra miniaturas, la foto completa y los niveles detectados. Filtra por alertas o revisión pendiente, comprueba los contornos y registra la revisión humana. Las marcas no alteran el índice ni el diagnóstico original. Exporta CSV total o filtrado. Las flechas del teclado recorren las fotos. «Limpiar pasillo» elimina definitivamente el recorrido guardado, sin borrar los originales del computador. Consulta la [guía del cliente](../Aplicacion_Cliente/README.md).

## Equipo: analizar y revisar

1. Toma fotos frontales o casi frontales, con apoyos visibles y sin reflejos fuertes. No hay un ángulo máximo validado.
2. Carga fotos JPG, PNG o WebP, hasta 10 MB cada una; el lote admite hasta 50 fotos y 500 MB.
3. Analiza el lote y comprueba los contornos. La confianza inicial es 0,60 y puede ajustarse desde 0,25.
4. Usa Original, Niveles, Bordes y Comparar; descarga el resultado cuando lo necesites.

El modelo oficial se selecciona automáticamente. La app no detecta automáticamente personas, obstáculos ni completitud: revisa tú la visibilidad. Un nivel no detectado no demuestra que esté vacío.

| Resultado | Lectura |
|---|---|
| Reponer | Índice visual menor a 52/100, cuando la señal permite decidir. |
| Suficiente | Índice desde 52/100 sin abstención; no certifica stock. |
| Revisar | Recorte o señal ambigua; puede ocultarse el índice. |

Los niveles se numeran de abajo hacia arriba. El mapa fucsia muestra evidencia visual; la vista de bordes filtrados permite inspeccionar Canny y la exclusión de estructura. Carteles y fondos pueden activar la señal y productos lisos pueden producir poca. El índice no es porcentaje físico de stock ni conteo de productos.

Las fotos se procesan localmente. La sesión puede guardarse en el navegador y eliminarse desde la app; no se incorpora al entrenamiento. Los resultados de revisiones anteriores se invalidan para volver a analizar las fotos con el algoritmo actual.

## Si hay un problema

Extrae el paquete completo, conserva sus archivos juntos y espera la preparación inicial de dependencias. Con Docker, comprueba que Docker Desktop esté activo. Si el análisis tarda demasiado o rechaza la foto, usa una imagen más pequeña. Si el resultado no coincide con la foto, revisa contornos y visibilidad antes de utilizar la alerta.

[Cómo funciona](Guia_para_entender_el_proyecto.md) · [Modelo y límites](Modelo_V3_actual.md) · [Línea A](../Aplicacion/Documentacion/LINEA_A_20261108.md).
