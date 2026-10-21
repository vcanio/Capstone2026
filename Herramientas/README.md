# Programas y herramientas del proyecto

| Carpeta | Para qué sirve | Dónde empezar |
|---|---|---|
| `Modelos/` | Código del laboratorio: panel, importación de CVAT, preparación de datos, entrenamiento, inferencia y pruebas automatizadas. | [Uso del panel](Modelos/README.md) y [script de entrenamiento](Modelos/entrenar_niveles.py). |
| `Datos/` | Comprobación de inventarios, integridad y estado de los lotes. | [Mantenimiento de Datos](Datos/README.md). |
| `Demo_lite/` | Código de Walmart Visión, la aplicación para probar los cuatro modelos V1/V2 con fotos propias. La carpeta conserva su nombre de desarrollo. | [Cómo usar Walmart Visión](Demo_lite/LEEME.md). |
| `CVAT/` | Scripts para iniciar CVAT y el acceso privado del equipo; incluye la instalación de CVAT. | `CVAT/iniciar_acceso_privado_equipo.ps1`, desde la raíz del proyecto. |
| `Informes/` | Generación del informe intermedio, la planificación visual y la guía de trabajo en equipo. | [Documentación del proyecto](../Documentacion/README.md). |
| `Reproducibilidad/` | Scripts para instalar activos, repetir ensayos, empaquetar y verificar la publicación. | [Preparación y reproducción](Reproducibilidad/README.md). |

`verificar_proyecto.py` comprueba datos, enlaces y exportaciones. Los modelos generales se organizan en `Modelos/` desde la raíz; esta carpeta `Herramientas/Modelos/` contiene el código que los utiliza. El manifiesto y las evidencias de verificación están en [reproducibilidad](../reproducibilidad/README.md).

Los archivos `.py` son código y los `.ps1` son iniciadores de PowerShell. Los archivos `test_*.py` verifican el funcionamiento. Las carpetas `__pycache__` son cachés generadas por Python.

Las pruebas del panel se agrupan en Modelos/tests. Para comprobar datos, enlaces de documentación y las exportaciones compartidas desde la raíz:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Herramientas/verificar_proyecto.py
```

Para **entregar la demo**, usar el ZIP preparado en [Entregables](../Entregables/README.md). Para **guardar fotografías**, usar [Datos](../Datos/README.md). Los pesos generales están en `Modelos/preentrenados/` desde la raíz; los entrenados están en cada ensayo de `Experimentos/`.
