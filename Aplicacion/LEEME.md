# Walmart Visión V3

## Mesa de revisión del equipo · 9/11/2026

Esta entrega incluye revisión rápida por foto, nivel o zona, varios fallos por imagen, atajos A/F/Enter/Z y revisión durante el análisis del lote. Abre **REVISION_EQUIPO.md** (en Documentacion/ en la copia de desarrollo) para el flujo completo y la comparación antes/después. **Descargar lote** guarda originales, incidencias, resultados y resumen; **Abrir lote de revisión** permite recuperarlos en otro equipo o versión. Las marcas se guardan localmente y no se envían al entrenamiento.

Walmart Visión detecta niveles en fotografías de góndolas y muestra una estimación experimental de cobertura del frente. Incluye el modelo V3 vigente y funciona localmente.

## Iniciar

**Windows:** extrae todo el ZIP y abre `iniciar.cmd`. La primera preparación necesita Internet para instalar las dependencias. Después abre http://127.0.0.1:8095 si no se abre automáticamente.

**macOS:** instala y abre Docker Desktop, extrae el ZIP y sigue los pasos de `DOCKER.md`. La primera construcción necesita Internet.

## Analizar fotos

1. Sube hasta 50 fotos JPG, PNG o WebP de hasta 10 MB cada una y 500 MB en total por lote. Usa tomas frontales o casi frontales, nítidas y con el tramo completo visible.
2. Pulsa **Analizar fotos**. La confianza inicial de detección es 60 % y puede ajustarse desde 25 %. Una confianza menor puede recuperar niveles, pero también producir detecciones incorrectas.
3. Revisa cada contorno y su confianza de detección. Usa las vistas **Original**, **Niveles**, **Bordes** y **Comparar** para contrastar el resultado. Puedes marcar una foto analizada para revisión y descargar las seleccionadas.

Las fotos se procesan localmente y no se incorporan al entrenamiento. La sesión del lote, incluidas las fotos, puede guardarse en el navegador de este equipo para recuperarla; se puede borrar desde las opciones de la galería.

## Interpretar los resultados

El modelo detecta una clase: **Nivel**. Puede omitir niveles o dibujar contornos incorrectos; revisa la fotografía antes de tomar decisiones. La confianza de detección no es ocupación. Si no hay detecciones, eso no significa que la góndola esté vacía.

El algoritmo actual es **Línea A**: índice visual de 0 a 100, con umbral **52** (Reponer por debajo; Suficiente desde 52, salvo revisión). Comparte normalización entre los niveles y penaliza huecos continuos. Es un índice experimental, no porcentaje físico de stock. El ajuste preliminar se evaluó con máscaras humanas; falta validación independiente suficiente de quiebres reales y del flujo completo. Se mantienen los avisos por recorte y señal ambigua. Consulta `Documentacion/LINEA_A_20261108.md`.



La aplicación no detecta automáticamente personas ni obstáculos. Revisa las zonas tapadas y fuera del encuadre; un resultado de «solo zona visible» no certifica el nivel completo. Se conocen omisiones de algunos superiores vacíos y contornos superiores demasiado altos. La reserva final de prueba no se ha evaluado.
