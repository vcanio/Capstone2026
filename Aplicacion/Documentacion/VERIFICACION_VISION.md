> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../Modelos/Actual/README.md).

# Verificación de Walmart Visión · 20 de octubre de 2026

La entrega conserva los cuatro pesos V1/V2 y la revisión 2 del análisis de bordes. El manifiesto identifica procedencia, clases y SHA-256 por modelo, y verifica los dos módulos de bordes. No incluye fotografías ni conjuntos de entrenamiento o evaluación.

Se ejecutaron 43 pruebas automatizadas: 15 de inferencia y HTTP, 5 de transiciones de interfaz, 13 de bordes y 10 de preparación del laboratorio. Las pruebas de interfaz ejecutan el JavaScript real y comprueban el filtro V1/V2, las clases, las cuatro vistas, la limpieza de resultados, los cambios de parámetros y la navegación por teclado.

Se verificó inferencia CPU desde el ZIP extraído con los cuatro modelos, con y sin bordes. Los estados y confianzas de YOLO se mantienen entre métodos. Se revisó la interfaz local en escritorio y a 390 px de ancho, con una fotografía real, comparación y mapas de señal. Los contenedores de imagen inicialmente vacíos permanecen ocultos hasta tener una imagen válida.

El ZIP pasa la prueba de integridad y los hashes de sus cuatro pesos coinciden con los best.pt del laboratorio. El cuaderno externo y el incluido son iguales y sus celdas Python tienen sintaxis válida. Los archivos de preparación Windows conservan saltos CRLF.

La instalación inicial requiere Internet y descarga dependencias de sus fuentes oficiales. No se ejecutó este cuaderno en una sesión real de Colab ni se comprobó esta entrega en otro computador físico. Los registros de verificación de esta publicación se conservan localmente en .publicacion/vision_qa/.
