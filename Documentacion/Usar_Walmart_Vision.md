# Usar Walmart Visión V3

La entrega vigente reúne la app cliente y la mesa de revisión del equipo. Ambas usan YOLO V3 para delimitar niveles y Línea A v2.2 para estimar la disponibilidad visual. [Descarga del MVP](../Entregables/README.md).

## Abrir

1. En Windows x64, extrae el ZIP completo y abre `iniciar_cliente.cmd` (8098) o `iniciar_equipo.cmd` (8095). La primera ejecución necesita Internet para preparar las dependencias.
2. Si usas un clon, los iniciadores están en `Aplicacion_Cliente/` y `Aplicacion/`. También puedes seguir la [instalación manual](../README.md#instalación-manual-y-configuración).
3. Para la app del equipo en Docker, consulta la [guía Docker](../Aplicacion/DOCKER.md). El Compose conjunto requiere ajustar el almacenamiento de SQLite para arrancar el cliente.

## Cliente

- Pulsa **Probar un pasillo de ejemplo** para abrir los [ocho casos incluidos](../Aplicacion_Cliente/ejemplos/README.md), o carga fotos JPG, PNG o WebP.
- Usa **Con alertas**, **Requieren revisión** o **Sin alertas** para filtrar las fotos. **Huecos** ayuda a localizar espacios sin producto visible. Las flechas recorren las fotos.
- Descarga el CSV del filtro o del recorrido. Los reportes Excel y PDF usan el historial del servidor. El cliente muestra los resultados del análisis y el historial se guarda en el navegador y en SQLite. [Guía del cliente](../Aplicacion_Cliente/README.md).

## Equipo

1. Carga fotos JPG, PNG o WebP, de hasta 10 MB y 24 megapíxeles por foto. El visor admite hasta 50 fotos y 500 MB por lote.
2. Pulsa **Analizar fotos** y comprueba los contornos. La confianza inicial de YOLO es 0,60 y puede ajustarse desde 0,25.
3. Usa **Original**, **Niveles**, **Bordes** y **Comparar**. Puedes registrar incidencias y descargar un lote ZIP para seguir la revisión. [Guía del equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md).

## Interpretar los resultados

| Resultado | Lectura |
|---|---|
| **Reponer** | El índice está por debajo de 52 o hay un hueco importante en el frente, con evidencia suficiente para decidir. |
| **Suficiente** | El índice es 52 o más y la señal permite aceptar la lectura. |
| **Revisar** | El nivel está recortado o la imagen aporta señales dudosas, por ejemplo un frente oscuro o una obstrucción. |
| **Foto no evaluable** | La captura tiene un problema grave de calidad o una persona tapa la góndola. Toma otra foto. |

Usa tomas frontales o casi frontales y procura que se vea todo el tramo. Un nivel vacío puede contener una máscara, porque YOLO busca repisas. Si el sistema no detecta niveles, revisa el encuadre antes de tomar una decisión. El índice describe solo la disponibilidad visible en la foto.

Las fotos se procesan localmente y quedan fuera del entrenamiento. **Limpiar pasillo** elimina el recorrido guardado por el cliente, incluidos sus registros en el servidor si está disponible. Los archivos de origen en tu equipo se conservan.

## Si hay un problema

Extrae el paquete completo, conserva sus archivos juntos y espera la preparación inicial de dependencias. Con Docker, comprueba que Docker Desktop esté activo. Si el análisis tarda demasiado o rechaza la foto, usa una imagen más pequeña. Si el resultado no coincide con la foto, revisa contornos y visibilidad antes de utilizar la alerta.

[Cómo funciona](Guia_para_entender_el_proyecto.md) · [Modelo y límites](Modelo_V3_actual.md) · [Criterio del umbral 52](Justificacion_umbral_52.md).
