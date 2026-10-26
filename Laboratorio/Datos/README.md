# Mantenimiento de Datos

`verificar_datos.py` comprueba el catálogo y sus inventarios sin escribir archivos. Solo necesita Python 3.11 o posterior y su biblioteca estándar.

Desde la raíz:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Herramientas/Datos/verificar_datos.py
& ./.venv-modelo/Scripts/python.exe -m unittest discover -s Laboratorio/Datos
```

Comprueba cantidades, identificadores y rutas registradas, SHA-256, coherencia entre inventario y manifest, imágenes sin registrar en lotes pendientes, permisos y reparto de esos lotes, separación de escenas del set vigente y hashes de la copia anotada. En la estructura consolidada comprueba que V1 contiene exactamente las imágenes registradas, sin duplicados. No sustituye la revisión visual: la similitud entre tomas y los grupos de escena se revisan antes de repartir.

Si falla, corregir la procedencia o el registro; no recalcular hashes para ocultar un cambio inesperado. La herramienta no importa a CVAT ni aprueba datos para entrenamiento.

[Flujo común](../../Datos/README.md) · [Catálogo de lotes](../../Datos/Registros/lotes.json).

## Laboratorio de partición y mantenimiento

| Programa | Alcance |
|---|---|
| `particionar_lider_express.py --verify` | Partición V2 congelada de 296 imágenes. Requiere Shapely, disponible en `.venv-modelo`. |
| `particionar_v3_458.py --verify` | Las 458 imágenes V3, familias, escenas, hashes y listas 327/68/63. |
| `ordenar_registros_20261023.py --verify` | Conservación de registros después de archivar pruebas retiradas. Solo en el equipo que guarda su respaldo local. |
| `ordenar_proyecto_20261023.py --verify` | Conservación de archivos protegidos, temporales archivados y checkout Git tras la limpieza general. Requiere Python 3.12 y el respaldo local de esa operación. |

Los scripts de limpieza son operaciones fechadas y rechazan aplicar otra vez sobre un recibo existente. No constituyen un comando general para borrar carpetas. [Mapa del proyecto](../../Documentacion/Desarrollo/Mapa_del_proyecto.md).
