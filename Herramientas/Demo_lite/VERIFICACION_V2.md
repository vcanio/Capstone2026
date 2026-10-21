# Verificación de Walmart Lite V2 con bordes

> **Registro histórico · Lite V2 anterior al cambio de nombre y visor de Walmart Visión.** Las comprobaciones vigentes de esa nueva entrega están en [Verificación de Walmart Visión](VERIFICACION_VISION.md); su instalación se explica en la [guía de uso](../../Documentacion/Usar_Walmart_Vision.md). Véase el [índice histórico](../../Documentacion/Historico/README.md).

Esta entrega incorpora los dos modelos V1 históricos y los dos V2 base. El manifiesto
incluye la procedencia y el SHA-256 de cada best.pt. La interfaz muestra las clases
del modelo elegido; V2 base no reconoce no_evaluable.

La revisión con bordes incluye el mismo Analyzer y script de detección de bordes del laboratorio
en disposición autónoma. El manifiesto verifica sus dos archivos de código además
de los cuatro pesos. La tabla informa área y ancho con señal experimental, conserva
los estados YOLO y no asigna porcentajes a niveles sin medición. Las fotografías
y los tres mapas resultantes se procesan en memoria, sin escribir fotos en disco.

Comprobaciones de esta revisión: 15 pruebas de Lite, 13 del algoritmo de detección de bordes y
10 del preparador. Se comprobó inferencia real con los cuatro modelos, con y sin bordes, desde el
ZIP extraído. Los estados y confianzas YOLO se conservaron. La interfaz se revisó
en escritorio y móvil, incluyendo ambos métodos y los tres mapas.

La revisión del 20 de octubre de 2026 incluye pruebas del preparador y de la demo,
integridad de los pesos y comprobación de inferencia CPU en una copia separada.
El resultado detallado de la preparación de publicación queda en
reproducibilidad/VERIFICACION.md del repositorio.

La instalación automática sigue usando un Python privado y necesita Internet en
el primer inicio. No se ejecutó el cuaderno en una sesión real de Colab y no se
afirma haber probado esta entrega en otro computador físico.
