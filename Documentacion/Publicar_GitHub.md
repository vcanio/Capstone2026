# Publicar Walmart Visión

La Release `walmart-vision-2026-10-20` contiene un único activo público: **Walmart_Vision_20261020.zip**. Incluye el visor, cuatro pesos V1/V2, análisis de bordes, iniciadores e instrucciones de Windows y el cuaderno de Colab. Los datos e informes del laboratorio se comparten por separado.

## Preparar y comprobar

```powershell
python Herramientas/Modelos/empaquetar_demo_lite.py --perfil v2
python Herramientas/Reproducibilidad/empaquetar_publicacion.py --solo-codigo --git "C:/Program Files/Git/cmd/git.exe"
```

El paquete queda en `Entregables/Walmart_Vision_20261020.zip`, con su SHA-256 al lado. El checkout revisable está en `.publicacion/repositorio/`. Los empaquetadores no hacen commit, push ni publicación y no modifican credenciales.

Revisar los cambios y ejecutar las pruebas de `Herramientas/Demo_lite/`, de bordes y del preparador. Extraer el ZIP en una carpeta nueva, comprobar sus hashes y ejecutar inferencia con ambos métodos. Verificar el visor y el cuaderno incluido. Actualizar la entrada demo de `reproducibilidad/artefactos.json` con el nombre, URL, tamaño, hash y archivos del ZIP final; conservar las entradas históricas de los paquetes del laboratorio.

## Publicar

1. Revisar el diff del checkout, hacer commit de código y documentación y push a main, sin forzar.
2. Crear la Release con tag `walmart-vision-2026-10-20` sobre ese commit y título **Walmart Visión · V1 y V2**. Utilizar las [notas preparadas](Notas_Release_Walmart_Vision_20261020.md) y añadir el SHA-256 del ZIP.
3. Adjuntar únicamente `Walmart_Vision_20261020.zip` desde `.publicacion/releases/` y publicar. Conservar la release anterior y sus activos históricos.
4. Descargar el activo publicado y comprobar su SHA-256 contra el ZIP verificado. Extraer todo y abrir `Walmart_Vision/iniciar.cmd`.

Los archivos Source code añadidos automáticamente por GitHub no contienen los pesos ni sustituyen el ZIP. No reutilizar el nombre de un activo publicado con contenido distinto. La aplicación mantiene su carácter de prototipo y sus límites se explican en las notas.

## Paquetes del laboratorio

Los paquetes de datos, exportaciones, modelos/resultados e informe permanecen en `.publicacion/paquetes_desarrollo/`, con metadatos de integridad y copias históricas. Compartirlos por separado para desarrollar; el [preparador](Replicar_proyecto.md) los instala con `--assets RUTA_A_LOS_ZIP`. No incluir en Git pesos, ZIP, entornos, fotografías, archivos .env ni accesos personales.
