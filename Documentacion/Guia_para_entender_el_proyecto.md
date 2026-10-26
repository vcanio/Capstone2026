# Cómo funciona Walmart Visión

Walmart Visión analiza una fotografía para ayudar a revisar posibles faltantes visibles por nivel de góndola. La versión V3 está integrada y en pruebas locales; su nueva release sigue pendiente.

## Dos operaciones distintas

**Primero localiza los niveles.** El modelo YOLO26n-seg V3 reconoce una sola clase, `Nivel`, y produce una máscara del área útil de cada repisa. Puede delimitar una zona aunque esté vacía.

**Después estima la ocupación.** Otro algoritmo busca bordes, cambios de color y textura dentro de esas máscaras. La estimación combina **70 % de superficie con señal y 30 % de cobertura horizontal**.

La app interpreta esa señal junto con la visibilidad indicada para mostrar Reponer, Suficiente o Revisar. Estas decisiones no son clases aprendidas por el modelo de niveles.

## Qué mide el porcentaje

Es una estimación visual del área detectada, no una proporción comprobada de productos o unidades. No mide lo que hay detrás de la primera fila ni consulta inventario.

El umbral experimental es 30 %: por debajo se señala Reponer y desde ese valor Suficiente, cuando el alcance permite emitir esa lectura. Sigue pendiente calibrar y evaluar la ocupación en V3.

## Para qué sirve el mapa de señal

El amarillo representa zonas que activan el análisis de bordes, color y textura. Los envases pueden producir esa señal, igual que un cartel o un fondo con dibujos.

Un superior vacío con un cartel puede generar una señal alta. La app incluye una regla conservadora: cuando al menos el 95 % de la señal ponderada de superficie se concentra en la mitad superior del nivel, conserva el cálculo bruto para diagnóstico y muestra **Revisar · señal ambigua**, sin presentar un porcentaje de ocupación.

Esta regla evita afirmar disponibilidad en ese patrón. No identifica carteles ni demuestra que el nivel esté vacío; también puede pedir revisión en productos cuya señal se concentre arriba.

## Por qué se pregunta por la visibilidad

El entrenamiento incluyó imágenes con obstáculos y recortes para aprender a delimitar niveles en esas condiciones. El modelo no tiene una salida entrenada que clasifique automáticamente la visibilidad.

Por eso la persona usuaria indica si la góndola está completa, recortada o tapada. Un recorte limita la lectura a lo visible; un objeto suspende la medición y una persona tapando pide otra foto sin mostrar contornos ni ocupación.

## Cómo se define el nivel superior

Las anotaciones se apoyan en la superficie sobre el portaprecio. En superiores sin techo físico claro se utiliza la mediana de las alturas de los niveles inferiores del mismo tramo. Si la proyección sale del encuadre, la anotación se recorta y se marca parcial.

En la app se conservan las máscaras predichas: **la mediana no se recalcula ni se impone durante la inferencia**. El modelo puede desviarse de ese criterio.

## Qué aprendió el modelo actual

El afinado vigente usó 113 fotos seleccionadas de entrenamiento, con refuerzos de papeles, huevos y superiores vacíos, más ejemplos de repaso. La validación se conserva separada y las 63 fotos de test siguen reservadas.

Las métricas del modelo describen su segmentación de niveles. No demuestran precisión de ocupación, detección automática de obstáculos ni mejora global frente al modelo padre. Consulta la [ficha actual](Modelo_V3_actual.md) para los resultados y las limitaciones conocidas.

[Usar la app](Usar_Walmart_Vision.md) · [Datos actuales](../Datos/README.md) · [Inicio](../README.md)
