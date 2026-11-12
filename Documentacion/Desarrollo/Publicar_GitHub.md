# Publicar Walmart Visión

La entrega vigente es la [prueba de cliente y equipo del 11/11](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-11). El código público contiene las apps, el único modelo oficial operativo, el laboratorio, sus pruebas, guías y resúmenes de evidencia. Datasets, fotografías privadas, credenciales, entornos, sesiones del navegador y respaldos locales quedan fuera.

## Preparar una entrega nueva

1. Crear un clon independiente de main. Comparar las fuentes locales y conservar los arreglos que ya existan en GitHub. No sincronizar `.publicacion/repositorio` ni mover sus worktrees.
2. Usar un manifiesto portable con un solo modelo oficial en `Aplicacion/modelos.json`; comprobar sus bytes, SHA-256 y `edge_sources`. Los candidatos y los pesos anteriores permanecen locales y en las entregas históricas.
3. Ejecutar las pruebas de datos, laboratorio, apps y empaquetado, además de `python Laboratorio/Reproducibilidad/verificar_publicacion.py` dentro del clon. Revisar enlaces, archivos preparados y posibles datos privados.
4. Generar un ZIP con nombre nuevo desde el clon:

```powershell
python Laboratorio/Reproducibilidad/empaquetar_apps_prueba.py --output Entregables/Pruebas/ARCHIVO_NUEVO.zip
```

El empaquetador incluye un solo motor compartido, modelo verificado, logo del cliente, iniciadores Windows, Compose, licencias y manifiesto SHA-256. Rechaza sobrescribir entregas existentes. Para una fecha/tag nuevos, actualizar los datos de la entrega en el empaquetador antes de construirla.

5. Extraer el ZIP en una carpeta nueva, comprobar todos los hashes y el arranque HTTP de ambas apps. La prueba de inferencia funcional usa una foto de desarrollo autorizada, nunca el test reservado. Informar por separado qué se comprobó en Docker y si hubo prueba física en Mac.
6. Hacer commit y push sin forzar. Esperar el CI del commit exacto. Crear una prerelease y un tag nuevos que apunten a ese commit, adjuntar ZIP y `.sha256`, y comprobar la descarga pública contra el archivo local.
7. Verificar que las releases anteriores conservan sus activos. Actualizar el estado de distribución y dejar un recibo de la operación sin publicar credenciales ni respuestas privadas completas.

## Alcance y antecedentes

Las apps distribuyen inferencia local. Sus fotos no se incorporan al entrenamiento. Solo Vicente inicia un futuro entrenamiento desde el panel, con plan nuevo a partir del oficial; publicar no inicia entrenamientos ni altera CVAT o particiones.

Conservar [LICENSE](../../LICENSE), [NOTICE.md](../../NOTICE.md), [LICENCIAS.md](../../LICENCIAS.md) y el acceso al código fuente correspondiente a cada entrega. Este acuerdo sobre el código no abre el dataset.

Las [distribuciones anteriores](../../Entregables/README.md#distribuciones-anteriores) y sus instrucciones fechadas se conservan como antecedentes. Los documentos académicos y las seis imágenes de demostración compartidas anteriormente mantienen su alcance; no representan una autorización para publicar el resto de las fotografías.
