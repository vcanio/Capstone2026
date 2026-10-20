# Mantenimiento de Datos

`verificar_datos.py` comprueba el catálogo y sus inventarios sin escribir archivos. Solo necesita Python 3.11 o posterior y su biblioteca estándar.

Desde la raíz:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Herramientas/Datos/verificar_datos.py
& ./.venv-modelo/Scripts/python.exe -m unittest discover -s Herramientas/Datos
```

Comprueba cantidades, identificadores y rutas registradas, SHA-256, coherencia entre inventario y manifest, imágenes sin registrar en lotes pendientes, permisos y reparto de esos lotes, separación de escenas del set vigente y hashes de la copia anotada. En la estructura consolidada comprueba que V1 contiene exactamente las imágenes registradas, sin duplicados. No sustituye la revisión visual: la similitud entre tomas y los grupos de escena se revisan antes de repartir.

Si falla, corregir la procedencia o el registro; no recalcular hashes para ocultar un cambio inesperado. La herramienta no importa a CVAT ni aprueba datos para entrenamiento.

[Flujo común](../../Datos/README.md) · [Catálogo de lotes](../../Datos/Registros/lotes.json).
