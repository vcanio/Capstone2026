# Preparación y reproducción de la entrega

Estos scripts usan la biblioteca estándar de Python 3.11/3.12, salvo el código
de entrenamiento que requiere las dependencias del laboratorio.

| Programa | Función |
|---|---|
| preparar.py | Descargar o leer ZIP locales, verificar hashes e instalar sin sobrescribir archivos diferentes. |
| verificar_publicacion.py | Auditar el checkout Git antes de descargar archivos grandes. |
| repetir_ensayo.py | Repetir V1 o V2 base en una carpeta nueva usando su copia congelada y sin consultar CVAT/test. |
| empaquetar_publicacion.py | Preparar el checkout y los activos desde el laboratorio del mantenedor. No hace commit ni push. |
| empaquetar_imagenes_demo.py | Preparar el ZIP separado de las seis imágenes reales/sintéticas seleccionadas, comprobando hashes y sin publicarlo. |

La [guía para replicar](../../Documentacion/Replicar_proyecto.md) explica instalación,
demostración y entrenamiento. La [guía para publicar](../../Documentacion/Publicar_GitHub.md)
describe commit, push, la Release de Walmart Visión y el ZIP de imágenes de ejemplo compartido en Drive. Los paquetes del
laboratorio se transfieren por separado y se instalan con --assets. El manifiesto de activos está
en [reproducibilidad/artefactos.json](../../reproducibilidad/artefactos.json).
El flujo diario de ramas, revisión y actualización está en
[Trabajo en equipo](../../Documentacion/Trabajo_en_equipo.md).

El [criterio de publicación](../../Documentacion/Publicar_GitHub.md#mantener-limpio-el-repositorio) mantiene en local los respaldos de partición, logs extensos y consultas completas de GitHub. El empaquetador los omite y la auditoría rechaza su incorporación; los [resúmenes de comprobaciones](../../Documentacion/Evidencias/README.md) permanecen públicos. La documentación de versiones anteriores se conserva con avisos históricos.

Pruebas del preparador y de CVAT opcional:

```powershell
python -m unittest discover -s Herramientas/Reproducibilidad/tests -v
```

La instalación no ejecuta scripts del ZIP. Rechaza rutas fuera del destino,
archivos adicionales, enlaces simbólicos en ZIP, hashes incorrectos y colisiones
con trabajo local. Si un archivo local cambió, conservarlo y usar una copia limpia.
