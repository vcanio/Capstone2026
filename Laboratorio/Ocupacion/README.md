# Calibración y evaluación de ocupación · V3

Herramientas de desarrollo para recolectar la referencia humana de disponibilidad por nivel, medir la línea base del estimador actual y calibrar el umbral de alerta conforme al enunciado del proyecto (`Historico/Contexto/Enunciado_Capstone_Deteccion_Espacios_Vacios_Gondolas.pdf`, archivo del entorno local; fuera de esta distribución).

## Iniciar el visor sandbox de Línea A vs Actual V3

Para inspeccionar visualmente el prototipo Línea A lado a lado frente al estimador anterior a la integraci?n (en casos clave, carpetas de prueba o cualquier foto subida), sin revelar muestras pendientes de etiquetado ciego:

```powershell
.\Laboratorio\Ocupacion\iniciar_visor_linea_a.cmd
```

O directamente con Python (GPU si está en `.venv-modelo` o CPU con `.entorno-py312`):

```powershell
& .\.venv-modelo\Scripts\python.exe .\Laboratorio\Ocupacion\visor_linea_a.py --port 8097 --open
```

## Iniciar el etiquetador rápido

Desde Windows (doble clic o consola en la raíz del proyecto):

```powershell
.\Laboratorio\Ocupacion\iniciar_etiquetador.cmd
```

O directamente con Python:

```powershell
& .\Aplicacion\.entorno-py312\Scripts\python.exe .\Laboratorio\Ocupacion\etiquetador_ocupacion.py --port 8096 --open
```

## Archivos de este módulo

| Archivo | Función |
|---|---|
| [`preparar_muestra.py`](preparar_muestra.py) | Genera la muestra congelada de 163 fotos (`93 val` + `70 train`) sin solapamiento de escenas ni acceso a `test`. |
| [`etiquetador_ocupacion.py`](etiquetador_ocupacion.py) | Servidor HTTP local (`127.0.0.1:8096`) con guardado atómico en JSON y CSV. |
| [`interfaz_etiquetador.html`](interfaz_etiquetador.html) | Estación visual de etiquetado ciego por teclado con recorte ampliado por nivel. |
| [`evaluar_linea_base.py`](evaluar_linea_base.py) | Calcula Precisión, Recall, F1 y tasa de revisión por nivel y por góndola sobre los niveles ya etiquetados. |
| [`prototipo_linea_a.py`](prototipo_linea_a.py) | Prototipo Línea A: normalización anclada de góndola, evidencia híbrida en cuerpo del nivel, penalización por hueco y abstención no atrapante. |
| [`evaluar_linea_a.py`](evaluar_linea_a.py) | Evalúa línea base V3 vs Línea A sobre etiquetas humanas (con calibración en `train` y reporte out-of-sample en `val`) y caché opcional de `04_Imagenes_para_pruebas`. |
| [`visor_linea_a.py`](visor_linea_a.py) | Servidor HTTP local (`127.0.0.1:8097`) que ejecuta `best.pt` y compara V3 actual vs Línea A con mapa de evidencia visual y carga de fotos propias. |
| [`interfaz_visor_linea_a.html`](interfaz_visor_linea_a.html) | Visor interactivo lado a lado (`Actual V3` vs `Línea A` vs `Mapa de evidencia`) con ajuste en vivo de umbral y confianza. |
| [`iniciar_visor_linea_a.cmd`](iniciar_visor_linea_a.cmd) | Iniciador directo en Windows del visor Línea A (prefiere GPU si está disponible y cae a CPU). |
| [`test_linea_a.py`](test_linea_a.py) | Pruebas unitarias sintéticas, HTTP sandbox y de regresión en imagen real para [`prototipo_linea_a.py`](prototipo_linea_a.py) y [`visor_linea_a.py`](visor_linea_a.py). |
| [`iniciar_etiquetador.cmd`](iniciar_etiquetador.cmd) | Iniciador directo en Windows. |

Los datos generados y las etiquetas humanas se guardan en `Datos/Preparados/V3/Calibracion_ocupacion_20261107/` (`Datos/Preparados/V3/Calibracion_ocupacion_20261107/README.md`, archivo del entorno local; fuera de esta distribución). No se modifica CVAT, el modelo `best.pt` ni las particiones.
