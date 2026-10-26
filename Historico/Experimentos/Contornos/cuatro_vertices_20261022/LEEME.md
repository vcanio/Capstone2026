> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../../Modelos/Actual/README.md).

# Prueba de contornos con cuatro vértices

La [documentación técnica y metodológica](../../../Documentacion/Desarrollo/Posprocesamiento_contornos_niveles.md)
explica la decisión, los umbrales, las evidencias y la evaluación pendiente.

El panel y Walmart Visión ajustan el contorno visible de cada nivel a un
cuadrilátero, con lados rectos y perspectiva. No se entrenaron modelos nuevos.

- En el panel del repositorio, vuelve a analizar la foto para generar una imagen
  nueva. Los resultados históricos conservan su dibujo original.
- Para probar la aplicación independiente, extrae por completo
  `Walmart_Vision_Cuatro_Vertices.zip` y abre `Walmart_Vision/iniciar.cmd`.
  Usa un puerto libre si ya hay otra instancia abierta.
- `comparacion.jpg` muestra los niveles 3 y 1 de la foto de las capturas.
  `despues.jpg` muestra la foto completa y `verificacion.json` las cuatro esquinas.

El ajuste modifica la visualización. Las clases, la confianza, la evaluación IoU
y el cálculo de ocupación siguen usando la predicción original de YOLO.
Si no se puede obtener un cuadrilátero convexo con suficiente coincidencia,
se conserva el contorno original. No corrige niveles omitidos o mal detectados.

Verificación: cuatro pruebas de geometría, quince de inferencia de la aplicación
y dos de integración del panel. En la foto de las capturas se ajustaron los seis
niveles. La comprobación visual es una prueba inicial, no una evaluación del
conjunto completo. La release publicada no fue modificada.
