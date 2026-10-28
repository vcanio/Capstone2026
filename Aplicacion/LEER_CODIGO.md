# Cómo leer el código de niveles y ocupación

Empieza por `ModelRunner.analyze()` en `inferencia.py`: coordina el recorrido
completo de una foto. Las funciones conservan sus nombres en inglés y las
explicaciones están en español.

## Recorrido de una foto

1. `read_photo()` abre los bytes, valida tamaño/formato y corrige la orientación.
2. `_load_model()` reutiliza el modelo YOLO y elige CPU o GPU disponible.
3. `model.predict()` localiza niveles y devuelve máscaras y confianzas.
4. `analyze_edges()` entrega cada máscara original al estimador de ocupación.
5. `occupancy_estimate()` interpreta la medición como Reponer, Suficiente o Revisar.
6. `apply_scope()` añade avisos cuando el nivel llega al borde de la foto.
7. `draw_result()` dibuja la lectura final sobre una copia de la foto.

La confianza filtra detecciones de niveles. El porcentaje de cobertura se
calcula después y no es la confianza de YOLO.

## Recorrido de un nivel

En `ocupacion_paulo.py`, `Analyzer` prepara los mapas de la foto una sola vez.
Después `Analyzer.analyze()` procesa cada nivel mediante estos pasos:

| Método | Responsabilidad |
|---|---|
| `_prepare_level()` | Validar la máscara, aplicar margen y formar la grilla. |
| `_exclude_structure()` | Intentar excluir rieles y conservar la referencia previa. |
| `_measure_cells()` | Medir bordes, gradiente, color y textura por celda. |
| `_measure_legacy_coverage()` | Conservar las métricas anteriores de área y ancho. |
| `_measure_v2()` | Calcular diagnóstico ponderado y reglas de revisión; activar cobertura frontal en V3. |
| `front_coverage()` | Contar columnas con respaldo en dos filas contiguas de la zona considerada. |
| `overlay()` | Dibujar el mapa fucsia de señal acumulada. |

`Parameters` agrupa la configuración de imagen y los métodos anteriores. Las
constantes al inicio del archivo nombran los umbrales experimentales de
interpretación. Los porcentajes usan 0–100; las fracciones, 0–1.

## Qué representa cada matriz

- **Máscara original:** alto × ancho de la foto, con 1 dentro del nivel y 0 fuera.
- **`region`:** máscara del recorte del nivel, con el margen exterior reducido.
- **`observed`:** píxeles de esa región tras excluir la estructura detectada.
- **`coverage`:** proporción de máscara por celda de la grilla.
- **`usable`:** celdas con cobertura suficiente para medir.
- **`raw_active`:** celdas activadas por la señal combinada antes del cierre morfológico.
- **`active`:** activación limpiada, usada para el área y el mapa fucsia.
- **`absolute_evidence`:** respaldo de bordes o de gradiente junto con textura.

`_LevelGrid` reúne la geometría y las celdas de un nivel. `_CellSignals` reúne
las características visuales. Los docstrings indican qué matrices están en
píxeles y cuáles están en filas × columnas de la grilla.

## Lectura vigente y diagnóstico anterior

V3 usa `front_signal_pct`: columnas del frente respaldadas por señal visual.
Asume lleno detrás del producto visible. La combinación antigua 70/30 sigue
disponible como `combined_signal_pct`, pero no determina el porcentaje mostrado
en V3. V1 y V2 mantienen sus lecturas anteriores por compatibilidad.

Las reglas de revisión pueden impedir presentar un porcentaje. La señal visual
no reconoce productos semánticamente y los umbrales requieren calibración.

El cuadrilátero de `geometria_niveles.py` es solo para el dibujo. La ocupación
siempre usa los píxeles de la máscara original, sin etiquetas superpuestas.
