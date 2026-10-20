# Programas y herramientas del proyecto

| Carpeta | Para qué sirve | Dónde empezar |
|---|---|---|
| `Modelos/` | Código del panel, importación de CVAT, preparación de datos, entrenamiento, inferencia y pruebas automatizadas. | [Uso del panel](Modelos/README.md). |
| `Datos/` | Comprobación de inventarios, integridad y estado de los lotes. | [Mantenimiento de Datos](Datos/README.md). |
| `Demo_lite/` | Código de la aplicación de inferencia para probar ambos modelos en otro computador. | [Cómo usar la demo](Demo_lite/LEEME.md). |
| `CVAT/` | Scripts para iniciar CVAT y el acceso privado del equipo; incluye la instalación de CVAT. | `CVAT/iniciar_acceso_privado_equipo.ps1`, desde la raíz del proyecto. |

Los archivos `.py` son código y los `.ps1` son iniciadores de PowerShell. Los archivos `test_*.py` verifican el funcionamiento. Las carpetas `__pycache__` son cachés generadas por Python.

Las pruebas del panel se agrupan en Modelos/tests. Para comprobar datos, enlaces de documentación y las exportaciones compartidas desde la raíz:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Herramientas/verificar_proyecto.py
```

Para **entregar la demo**, usar el ZIP preparado en [Entregables](../Entregables/README.md). Para **guardar fotografías**, usar [Datos](../Datos/README.md). Los pesos generales están en `Modelos/preentrenados/` desde la raíz; los entrenados están en cada ensayo de `Experimentos/`.
