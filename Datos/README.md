# Datos del proyecto

**Trabajo actual: V3, 458 imágenes para localizar áreas útiles de niveles.** Partición fijada en 327 entrenamiento, 68 validación y 63 prueba; revisión de anotaciones y exportación V3 pendientes.

| Carpeta | Qué contiene |
|---|---|
| [V3](V3/README.md) | Nuevos lotes: 122 originales de Líder 2 y 40 variantes de superior vacío. |
| [V2](V2/README.md) | Fuentes de Líder Express: 236 originales/A/B/C y 60 ediciones con obstáculos. Sus mismos archivos se usan en V3, tareas 27 y 24. |
| [V1](V1/README.md) | Primera etapa: 30 reales de desarrollo, 72 sintéticas y siete reservas. La copia revisada usada por los primeros ensayos tiene 91 activas. |
| [Registros](Registros/README.md) | Entrada a lotes, tareas CVAT, revisiones, particiones, versiones de datos e historial. |

La ruta física de una imagen conserva su procedencia. Reutilizarla con otro criterio no crea otra foto ni exige copiarla de V2 a V3. Las 458 de V3 suman 296 fuentes reutilizadas + 40 variantes D + 122 originales nuevos.

## Dónde consultar

- [Estado actual](Registros/estado_actual.json): alcance y referencias por tarea.
- [Lotes y procedencia](Registros/Lotes/README.md): inventarios, manifests, imágenes y prompts.
- [Partición de las 458 imágenes](Registros/Particiones/v3_458_20261023/README.md): familias, escenas, catálogo visual y listas.
- [Anotaciones y correcciones](Registros/CVAT/README.md).
- [Versiones de datos de ensayos anteriores](Registros/Versiones_modelos/README.md).

## Reglas de conservación

1. Cada lote conserva sus fotos y su inventario; los registros centrales los enlazan sin duplicarlos.
2. Las vistas de un tramo y sus variantes comparten escena y partición. El test queda reservado para evaluación final.
3. Los datos usados por un ensayo se conservan con su versión e integridad; una corrección requiere otra versión.
4. Borradores y vistas retiradas se archivan en `.resguardo/`, con recibo cuando se retiran de los registros operativos.
5. Las fotos de inferencia manual viven en `Experimentos/panel_pruebas/Subidas_panel/`, fuera de inventarios de entrenamiento.

## Verificar

Desde la raíz:

```powershell
.venv-cvat/Scripts/python.exe Herramientas/Datos/verificar_datos.py
.venv-modelo/Scripts/python.exe Herramientas/Datos/particionar_lider_express.py --verify
.venv-cvat/Scripts/python.exe Herramientas/Datos/particionar_v3_458.py --verify
```

Comprueban rutas, cantidades, hashes e aislamiento de escenas. No escriben anotaciones en CVAT ni inician entrenamiento.
