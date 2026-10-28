# Walmart Visión V3

Walmart Visión detecta niveles en fotografías de góndolas y muestra una estimación experimental de cobertura del frente. Incluye el modelo V3 vigente y funciona localmente.

## Iniciar

**Windows:** extrae todo el ZIP y abre `iniciar.cmd`. La primera preparación necesita Internet para instalar las dependencias. Después abre http://127.0.0.1:8095 si no se abre automáticamente.

**macOS:** instala y abre Docker Desktop, extrae el ZIP y sigue los pasos de `DOCKER.md`. La primera construcción necesita Internet.

## Analizar fotos

1. Sube fotos JPG, PNG o WebP de hasta 15 MB cada una. Usa tomas frontales o casi frontales, nítidas y con el tramo completo visible.
2. Pulsa **Analizar fotos**. La confianza inicial de detección es 60 % y puede ajustarse desde 25 %. Una confianza menor puede recuperar niveles, pero también producir detecciones incorrectas.
3. Revisa cada contorno y su confianza de detección. Usa las vistas **Original**, **Niveles**, **Bordes** y **Comparar** para contrastar el resultado. Puedes marcar una foto analizada para revisión y descargar las seleccionadas.

Las fotos se procesan localmente y no se incorporan al entrenamiento. La sesión del lote, incluidas las fotos, puede guardarse en el navegador de este equipo para recuperarla; se puede borrar desde las opciones de la galería.

## Interpretar los resultados

El modelo detecta una clase: **Nivel**. Puede omitir niveles o dibujar contornos incorrectos; revisa la fotografía antes de tomar decisiones. La confianza de detección no es ocupación. Si no hay detecciones, eso no significa que la góndola esté vacía.

La cobertura estimada usa señal de bordes, color y textura dentro de los niveles. Es experimental y no identifica productos de forma fiable ni mide el stock detrás del frente visible. La aplicación muestra **Reponer** bajo el umbral experimental de 30 %, **Suficiente** desde 30 % cuando hay una lectura válida y **Revisar** cuando la señal o el alcance son ambiguos. La medición no está calibrada para V3.

La aplicación no detecta automáticamente personas ni obstáculos. Revisa las zonas tapadas y fuera del encuadre; un resultado de «solo zona visible» no certifica el nivel completo. Se conocen omisiones de algunos superiores vacíos y contornos superiores demasiado altos. La reserva final de prueba no se ha evaluado.
