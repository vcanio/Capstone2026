# Datos del proyecto

**Estructura simétrica por tanda (`V1/` y `V2/`) más catálogo centralizado (`Registros/`).**

| Carpeta | Propósito | Contenido actual |
|---|---|---|
| [V1](V1/README.md) | **Primera tanda** · Criterio v1 (4 estados, tarea 16). | `Lider/`: 30 reales de desarrollo. `Sinteticas/`: 72 generadas. `Reservadas/`: 7 reales de reserva final. (91 activas en la copia revisada). |
| [V2](V2/README.md) | **Segunda tanda** · Criterio v2 (reposición y visibilidad, tareas 19 y 22). | [Líder Express · 236 imágenes](V2/lider_express_20261016/README.md) (59 reales + 177 variantes IA, tarea 19) y [Visibilidad limitada · 60 imágenes](V2/visibilidad_limitada_20261019/README.md) (60 sintéticas con obstáculos, tarea 22). |
| [Registros](Registros/README.md) | Catálogo de procedencia, inventarios, particiones y copias congeladas de anotaciones. | [lotes.json](Registros/lotes.json), [dataset_activo.json](Registros/dataset_activo.json), [Particiones](Registros/Particiones/lider_express_v2_20261019/README.md) y `Versiones_modelos/`. |

## Reglas de orden y trazabilidad

1. **Separación por etapa:** los datos de la primera iteración permanecen congelados en `V1/`; cada lote de la segunda etapa vive en `V2/<lote>_<AAAAMMDD>/` con sus imágenes, prompts, `inventario.csv`, `manifest.json` y `README.md`.
2. **Sin duplicados ni archivos intermedios:** cada lote conserva únicamente sus imágenes activas y registros definitivos. Los borradores, muestras previas y carpetas intermedias se resguardan en `.resguardo/orden_v1_v2_20261019` (archivo local histórico, fuera de la distribución).
3. **Partición sin fuga de escenas:** todas las vistas de un mismo tramo físico, sus variantes A/B/C y sus ediciones con obstáculos comparten grupo de escena y partición (`train`, `val` o `test`).
4. **Inferencia manual aislada:** las fotografías subidas desde **Probar una foto** en el panel se almacenan en `Experimentos/panel_pruebas/Subidas_panel/`, fuera de `Datos/` y de cualquier inventario de entrenamiento.

## Verificación automática

Desde la raíz del proyecto:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Herramientas/Datos/verificar_datos.py
& ./.venv-modelo/Scripts/python.exe ./Herramientas/Datos/particionar_lider_express.py --verify
```

Ambos comandos comprueban rutas, conteos, hashes SHA-256 y aislamiento de escenas sin modificar archivos.
