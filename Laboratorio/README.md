# Laboratorio de desarrollo · V3

Herramientas para mantener Walmart Vision y continuar el trabajo desde el best.pt vigente. La aplicación para analizar fotografías está en [Aplicacion](../Aplicacion/README.md).

| Carpeta | Uso |
|---|---|
| [Modelos](Modelos/README.md) | Panel, preparación V3, entrenamiento, predicción y pruebas. |
| [Datos](Datos/README.md) | Integridad, inventarios y particiones. |
| [CVAT](CVAT) | Inicio y mantenimiento de la instalación de anotación. |
| [Experimentos](Experimentos/README.md) | Afinado vigente, soporte de ocupación y registros del panel. |
| [Reproducibilidad](Reproducibilidad/README.md) | Empaquetado, preparación y comprobación de activos. |
| [Informes](Informes) | Generación de informes y material académico. |

Para abrir el panel usar [Modelos/abrir_panel.ps1](Modelos/abrir_panel.ps1). Abre siempre V3 estable: pruebas de fotos, resultados y preparación del próximo refuerzo desde su best.pt. El catálogo habitual usa solo exportaciones de la partición activa. Limpieza y comprobaciones del 30 de octubre (`Historico/Documentacion/Desarrollo/Limpieza_laboratorio_20261030.md`, archivo del entorno local; fuera de esta distribución).

Para iniciar sus servicios usar [Modelos/iniciar_panel.ps1](Modelos/iniciar_panel.ps1). Los entrenamientos se inician por el usuario desde el panel.

Desde la raíz del proyecto:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Laboratorio/Datos/verificar_particion_v3.py
& ./.venv-modelo/Scripts/python.exe ./Laboratorio/verificar_proyecto.py
```

El verificador general conserva la incidencia anterior de tres fuentes V1 ausentes. [Estado y mapa del proyecto](../Documentacion/Desarrollo/Mapa_del_proyecto.md) · [Histórico](../Historico/README.md).

## Clon público y pruebas

El clon incluye código y el modelo de inferencia, sin los datos privados necesarios para reproducir los entrenamientos. Las pruebas unitarias usan fixtures; las integraciones que requieren fotos o particiones locales se omiten explícitamente si esos activos no están disponibles. No generar fuentes sustitutas ni desactivar comprobaciones de integridad para hacerlas pasar. El verificador global conserva las tres fuentes V1 ausentes documentadas.

Para comprobar el laboratorio en Windows: establece `PYTHONPATH=Laboratorio/Modelos` y ejecuta `python -m unittest discover -s Laboratorio/Modelos/tests -v`. La ocupación de desarrollo tiene pruebas separadas en `Laboratorio/Ocupacion`. Estos comandos no inician entrenamientos reales.
