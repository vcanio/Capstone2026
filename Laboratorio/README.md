# Laboratorio interno de desarrollo · V3

Herramientas internas construidas para preparar datos, configurar entrenamientos y seguir visualmente métricas, curvas y resultados de los ensayos. Se conservan como apoyo técnico y trazabilidad del desarrollo. No forman parte del ZIP cliente/equipo ni se necesitan para usar las apps.

Los niveles se anotaron y revisaron en CVAT. Las predicciones del modelo se inspeccionaron mediante la [app de revisión del equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md); el [cliente](../Aplicacion_Cliente/README.md) es la entrega principal para consultar alertas visuales. [Metodología y alcance de cada herramienta](../Documentacion/Metodologia_desarrollo_y_revision.md).

| Carpeta | Uso |
|---|---|
| [Modelos](Modelos/README.md) | Panel interno, preparación V3, entrenamiento, métricas y pruebas. |
| [Datos](Datos/README.md) | Integridad, inventarios y particiones. |
| [CVAT](CVAT) | Inicio y mantenimiento de la instalación de anotación. |
| [Experimentos](Experimentos/README.md) | Afinado vigente, soporte de ocupación y registros del panel. |
| [Reproducibilidad](Reproducibilidad/README.md) | Empaquetado, preparación y comprobación de activos. |
| [Informes](Informes) | Generación de informes y material académico. |

Para abrir el panel usar [Modelos/abrir_panel.ps1](Modelos/abrir_panel.ps1). Abre el flujo V3 de preparación, entrenamiento y resultados. La inspección de fotografías se realiza en la app de revisión; un futuro refuerzo requiere un plan nuevo desde el best.pt vigente. El catálogo habitual usa solo exportaciones de la partición activa. Limpieza y comprobaciones del 30 de octubre (`Historico/Documentacion/Desarrollo/Limpieza_laboratorio_20261030.md`, archivo del entorno local; fuera de esta distribución).

Para iniciar sus servicios usar [Modelos/iniciar_panel.ps1](Modelos/iniciar_panel.ps1). Solo Vicente inicia los entrenamientos desde el panel.

Desde la raíz del proyecto:

```powershell
& ./.venv-modelo/Scripts/python.exe ./Laboratorio/Datos/verificar_particion_v3.py
& ./.venv-modelo/Scripts/python.exe ./Laboratorio/verificar_proyecto.py
```

El verificador general conserva la incidencia anterior de tres fuentes V1 ausentes. [Estado y mapa del proyecto](../Documentacion/Desarrollo/Mapa_del_proyecto.md) · [Histórico](../Historico/README.md).

## Clon público y pruebas

El clon incluye código y el modelo de inferencia, sin los datos privados necesarios para reproducir los entrenamientos. Las pruebas unitarias usan fixtures; las integraciones que requieren fotos o particiones locales se omiten explícitamente si esos activos no están disponibles. No generar fuentes sustitutas ni desactivar comprobaciones de integridad para hacerlas pasar. El verificador global conserva las tres fuentes V1 ausentes documentadas.

Para comprobar el laboratorio en Windows: establece `PYTHONPATH=Laboratorio/Modelos` y ejecuta `python -m unittest discover -s Laboratorio/Modelos/tests -v`. La ocupación de desarrollo tiene pruebas separadas en `Laboratorio/Ocupacion`. Estos comandos no inician entrenamientos reales.
