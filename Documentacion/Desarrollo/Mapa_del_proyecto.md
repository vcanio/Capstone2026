# Mapa del proyecto · V3

Organización actualizada el 11 de noviembre de 2026. La aplicación V3 y el laboratorio tienen entradas propias; el historial conserva las decisiones y resultados de versiones anteriores. Los antecedentes están archivados; véase el [cierre y las comprobaciones](Limpieza_orden_20261108.md).

Los datasets voluminosos usan una raíz externa configurable. El [catálogo y la guía de conexión](../../Datos/Registros/Almacenamiento/README.md) conservan las referencias de las exportaciones; [alcance y comprobaciones de la migración](Datos_externos_20261108.md). Las fuentes compartidas y una copia independiente de los bytes únicos permanecen en C: para recuperación. La app sigue siendo autónoma.

| Carpeta | Contenido y entrada |
|---|---|
| [Aplicacion](../../Aplicacion/README.md) | App del equipo V3, iniciador Windows y Docker, puerto 8095. |
| [Aplicacion_Cliente](../../Aplicacion_Cliente/README.md) | App cliente de prueba, alertas, revisión humana y CSV, puerto 8098. |
| [Laboratorio](../../Laboratorio/README.md) | Preparación, anotación, entrenamiento, evaluación y verificadores. |
| [Datos](../../Datos/README.md) | Fuentes, procedencia, anotaciones, exportaciones y particiones. |
| [Modelos](../../Modelos/Actual/README.md) | Acceso al best.pt vigente y recursos preentrenados. |
| [Entregables](../../Entregables/README.md) | Entrega conjunta de apps, SHA-256 e historial de distribución. |
| [Documentacion](../README.md) | Uso, arquitectura, criterios, métricas y limitaciones. |
| [Infraestructura](../../Infraestructura/README.md) | Servicios Docker y CVAT. |
| [Historico](../../Historico/README.md) | Antecedentes, ensayos retirados y manifiestos de entregas anteriores. |

## Trabajo vigente

- App: [Aplicacion/iniciar.cmd](../../Aplicacion/iniciar.cmd), puerto 8095; [manual](../Usar_Walmart_Vision.md).
- Laboratorio: [Laboratorio/Modelos/abrir_panel.ps1](../../Laboratorio/Modelos/abrir_panel.ps1), puerto 8090.
- Modelo: best.pt de `v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c`, [ficha pública](../Modelo_V3_actual.md) y registro local `.config-modelo/version_actual_v3.json`.
- Datos: [partición activa](../Estado_V3_actual.json) y selección `cierre_yolo_contornos_revisados_20261110`; el ensayo utilizó 256 imágenes de entrenamiento (203 reales/53 sintéticas), 1.298 polígonos train y 11 fotos de validación real con 55 polígonos. Test reservado.
- Ocupación local: Línea A, índice visual experimental 0–100 y umbral 52; [detalles y límites](../../Aplicacion/Documentacion/LINEA_A_20261108.md). El ZIP publicado el 5/11 conserva el estimador anterior.

## Fuentes compartidas e historial

`Datos/Fuentes` ofrece accesos locales a los lotes por procedencia. Los lotes utilizados en V3 están físicamente en `Datos/V3`; las rutas anteriores de los dos lotes de Líder Express en `Datos/V2` se conservan como enlaces locales, con montajes Docker explícitos. V1 conserva material de la primera etapa. Los datasets y planes congelados mantienen sus bytes y rutas registradas. Ver [Fuentes](../../Datos/Fuentes/README.md).

Los prefijos antiguos `Herramientas/`, `Experimentos/`, `Contexto/`, `reproducibilidad/`, `Documentacion/Historico/` y la instancia anterior de `.tmp/` disponen de enlaces de compatibilidad locales ocultos. No duplican contenido. Los identificadores históricos de API `Experimentos/...` se conservan; los nuevos accesos del explorador apuntan a las carpetas reorganizadas.

Los entornos `.venv-modelo` y `.venv-cvat`, la configuración local y los respaldos son recursos técnicos. `.publicacion/repositorio` es un checkout independiente y no fue sincronizado. El enlace externo de `.tmp/visibilidad_v2/node_modules` se conserva sin recorrerlo.

## Verificar y mantener

Ejecutar `Laboratorio/Datos/verificar_particion_v3.py` para la integridad V3 y `Laboratorio/verificar_proyecto.py` para el conjunto. El segundo conserva la incidencia previa de tres fuentes V1 ausentes; no equivale a una auditoría global aprobada.

Registro y comprobaciones de la reorganización (`Historico/Documentacion/Desarrollo/Reorganizacion_carpetas_20261026.md`, archivo del entorno local; fuera de esta distribución) · [Volver al inicio](../../README.md).
