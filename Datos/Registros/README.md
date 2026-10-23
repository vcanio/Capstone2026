# Registros: empezar aquí

**Vigente al 23/10/2026: V3, 458 imágenes, tareas 24, 27 y 28.** Se preparan datos para localizar áreas útiles con la clase `Nivel`. La partición está fijada en **327 entrenamiento / 68 validación / 63 prueba**; revisión de anotaciones y exportación V3 pendientes.

## Consultas habituales

| Necesito saber… | Abrir |
|---|---|
| Qué datos estamos preparando ahora | [Estado actual V3](estado_actual.json) |
| Cuáles son las 458 fotos y sus escenas | [Partición actual y catálogo visual](Particiones/v3_458_20261023/README.md) |
| Qué contiene cada tarea de anotación | [CVAT](CVAT/README.md) |
| De dónde proviene cada paquete de fotos | [Lotes](Lotes/README.md) · [Catálogo de procedencia](lotes.json) |
| Qué se corrigió y cómo se comprobó | [Revisiones de anotaciones](CVAT/revisiones/README.md) |
| Qué copia de datos corresponde a un ensayo anterior | [Versiones de datos para modelos](Versiones_modelos/README.md) |
| Qué quedó retirado o se conserva como antecedente | [Histórico y limpieza](Historico/README.md) |

## Qué guarda cada carpeta

```text
Registros/
  estado_actual.json        Punto de entrada del trabajo V3 actual
  lotes.json                Catálogo de procedencia de seis lotes
  CVAT/                     Registros de tareas y anotaciones
    revisiones/             Correcciones, planes y verificaciones
  Lotes/                    índice de lotes y registro heredado de V1
  Particiones/              Repartos congelados por familia y escena
  Versiones_modelos/        Copias de datos de los ensayos anteriores
  Historico/                Selecciones antiguas y tareas sustituidas
```

**Una foto puede aparecer en varios registros porque cada uno responde una pregunta diferente.** El lote indica su procedencia; CVAT, su tarea y anotaciones; la partición, su uso reservado; y una versión de datos, la copia concreta preparada para un ensayo. Esas referencias no se suman como fotos distintas.

Los inventarios recientes se conservan junto a sus imágenes en `Datos/V2/` o `Datos/V3/`. `Lotes/` los enlaza sin almacenar otra copia.

## Archivos heredados que siguen teniendo uso

Estos nombres se conservan porque los leen el panel, verificadores o ensayos anteriores:

| Archivo | Alcance exacto |
|---|---|
| [dataset_activo.json](dataset_activo.json) | Configuración histórica V1 de los primeros ensayos: 102 imágenes de procedencia, 91 activas tras revisión. **No identifica el V3 actual.** Los ensayos V2 consultan su propia versión. |
| [inventario.csv](inventario.csv) | Las 37 fuentes reales iniciales: 30 de desarrollo y siete reservadas. **No es el inventario de las 458.** |
| [reserva_evaluacion.json](reserva_evaluacion.json) | Reserva histórica de siete fotos y sus escenas, excluida del conjunto actual. La reserva V3 se consulta en su partición. |

`CVAT/organizacion.json` describe la organización V2 heredada que consulta el panel. Para V3 se usa `CVAT/criterio_v3.json`. Los registros son lecturas fechadas; los cambios posteriores en CVAT requieren una nueva consulta.

## Reglas para mantener el orden

1. Las fotos, variantes y prompts viven en su lote; aquí se guardan índices y evidencias de trazabilidad.
2. Vistas del mismo tramo y variantes comparten familia/escena/partición. No repartir al azar ni usar el test para ajustar modelos o umbrales.
3. Las correcciones llevan plan, respaldo y verificación. Las pruebas retiradas se identifican como históricas y no se vuelven a cargar.
4. Una versión usada por un ensayo conserva sus anotaciones, partición, exportación e integridad. Las modificaciones requieren otra versión.
5. Las cachés regenerables pueden limpiarse. Las vistas retiradas se archivan fuera de los registros operativos, con ubicación y hashes. No eliminar por extensión las imágenes o JSON de una versión.
6. Al agregar un lote, actualizar `lotes.json`, su índice y el estado actual cuando corresponda. Las aprobaciones para entrenar se gestionan explícitamente.

## Comprobaciones

Desde la raíz del proyecto:

```powershell
.venv-cvat/Scripts/python.exe Herramientas/Datos/verificar_datos.py
.venv-cvat/Scripts/python.exe Herramientas/Datos/particionar_v3_458.py --verify
.venv-cvat/Scripts/python.exe Herramientas/Datos/ordenar_registros_20261023.py --verify
```

El primero verifica los seis lotes; el segundo, las 458 imágenes y el aislamiento de escenas; el tercero, la conservación tras la limpieza. Ninguno escribe anotaciones en CVAT.
