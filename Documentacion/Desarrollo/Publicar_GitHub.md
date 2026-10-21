# Publicar Walmart Visión

La [Release vigente](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-docker-2026-10-21), `walmart-vision-docker-2026-10-21`, contiene **Walmart_Vision_Docker_20261021.zip** y su **.sha256**. Incluye el visor, cuatro pesos V1/V2, análisis de bordes, iniciadores Windows, archivos Docker para macOS y el cuaderno de Colab. La Release Windows del 20 de octubre se conserva. Los datos e informes del laboratorio se comparten por separado.

## Preparar y comprobar

```powershell
python Herramientas/Modelos/empaquetar_demo_lite.py --perfil v2
python Herramientas/Reproducibilidad/empaquetar_publicacion.py --solo-codigo --git "C:/Program Files/Git/cmd/git.exe"
```

El empaquetador de Visión genera ahora `Entregables/Walmart_Vision_Docker_20261021.zip`, con su SHA-256 al lado. El activo publicado `Walmart_Vision_20261020.zip` se conserva aparte. El checkout revisable está en `.publicacion/repositorio/`. Los empaquetadores no hacen commit, push ni publicación y no modifican credenciales.

Revisar los cambios y ejecutar las pruebas de `Herramientas/Demo_lite/`, de bordes y del preparador. Extraer el ZIP en una carpeta nueva, comprobar sus hashes y ejecutar inferencia con ambos métodos. Verificar el visor y el cuaderno incluido. Actualizar la entrada demo de `reproducibilidad/artefactos.json` con el nombre, URL, tamaño, hash y archivos del ZIP final; conservar las entradas históricas de los paquetes del laboratorio.

## Publicar una nueva versión

La preparación Docker del 21 de octubre se genera con `python Herramientas/Modelos/empaquetar_demo_lite.py --perfil v2 --output Entregables/Walmart_Vision_Docker_20261021.zip`. Contiene los archivos Docker además del visor y los modelos. Consultar [preparación y comprobación Docker](../../Herramientas/Demo_lite/DOCKER.md#preparación-desde-el-laboratorio). Esta versión ya se publicó y sus dos descargas se verificaron contra los archivos locales. Para una entrega posterior, usar un nombre y tag nuevos y actualizar los enlaces y el manifiesto después de publicarla; conservar los activos existentes. La creación local del ZIP no publica nada en GitHub.

1. Revisar el diff del checkout, hacer commit de código y documentación y push a main, sin forzar.
2. Preparar las notas, el tag y el título de la nueva versión con el alcance real de [verificación Docker](../../Herramientas/Demo_lite/VERIFICACION_DOCKER.md). Las [notas del 20 de octubre](Notas_Release_Walmart_Vision_20261020.md) corresponden a la entrega Windows anterior.
3. Adjuntar `Walmart_Vision_Docker_20261021.zip` y su SHA-256 como archivos nuevos. Conservar la release anterior y sus activos históricos. El empaquetador general `empaquetar_publicacion.py`, fuera de `--solo-codigo`, todavía usa el activo del 20 de octubre: para esta nueva distribución preparar explícitamente el ZIP indicado y actualizar el manifiesto con la URL real de publicación.
4. Descargar el activo publicado y comprobar su SHA-256 contra el ZIP verificado. Extraer todo y comprobar el recorrido Docker de `DOCKER.md`, además del iniciador Windows cuando corresponda.

Los archivos Source code añadidos automáticamente por GitHub no contienen los pesos ni sustituyen el ZIP. No reutilizar el nombre de un activo publicado con contenido distinto. La aplicación mantiene su carácter de prototipo y sus límites se explican en las notas.

## Compartir las imágenes de demostración desde Drive

Se preparó una selección confirmada de **tres fotos reales y tres variantes sintéticas**, documentada en [Imágenes para probar Visión](../Usar_Walmart_Vision.md#probar-con-imágenes-de-ejemplo). Es una excepción limitada a esas seis imágenes; el dataset completo sigue distribuyéndose por separado. El ZIP de la aplicación publicado conserva su contenido.

Desde el laboratorio con las fuentes disponibles, ejecutar:

```powershell
python Herramientas/Reproducibilidad/empaquetar_imagenes_demo.py
```

El script comprueba las seis fuentes declaradas y crea `.publicacion/releases/Walmart_Vision_Imagenes_Demo_20261020.zip`, con su SHA-256 al lado. El ZIP contiene las carpetas `reales` y `sinteticas`, un LEEME y el manifiesto de procedencia. No incluye pesos, credenciales, el dataset completo ni imágenes de la reserva final. Una copia nueva del código necesita las fuentes de desarrollo para regenerarlo; el usuario solo necesita descargar el ZIP resultante.

La ubicación de descarga es la [carpeta de imágenes de prueba en Google Drive](https://drive.google.com/drive/folders/1z0-GNiRUJcVwbjLVkiDc20G2F8f9QASS?usp=sharing). Mantener allí el ZIP con permiso de lectura para cualquier persona con el enlace y la descarga habilitada. El README y las guías enlazan esa carpeta; no hace falta adjuntar las imágenes a una Release de GitHub.

Conservar el nombre, el contenido y el SHA-256 de la versión publicada. El LEEME incluido se conserva como fuente versionada en `Documentacion/Ejemplos/LEEME_imagenes_demo_20261020.txt`, separado de las guías de descarga que pueden actualizarse. Para un conjunto diferente, crear otra versión del ZIP y del manifiesto, actualizar los enlaces y comprobar la descarga sin iniciar sesión. El commit y push publican los cambios de documentación; la subida del ZIP a Drive es una operación separada.

## Paquetes del laboratorio

Los paquetes de datos, exportaciones, modelos/resultados e informe permanecen en `.publicacion/paquetes_desarrollo/`, con metadatos de integridad y copias históricas. Compartirlos por separado para desarrollar; el [preparador](Replicar_proyecto.md) los instala con `--assets RUTA_A_LOS_ZIP`. No incluir en Git pesos, ZIP, entornos, fotografías, archivos .env ni accesos personales.

## Mantener limpio el repositorio

Publicar código, pruebas, guías vigentes y resúmenes de resultados que respalden el proyecto. El material obligatorio de `Fase 1/` se conserva en Git. Las guías de versiones anteriores se agrupan en `Documentacion/Historico/` y llevan un aviso con un enlace a la documentación vigente; consultar el [índice histórico](../Historico/README.md).

Los respaldos `Datos/Registros/Particiones/**/respaldo_registros/`, los logs bajo `Documentacion/Evidencias/` y las respuestas completas `consulta_github_*.json` de esa carpeta quedan solo en local. Actualizar los [resúmenes públicos](../Evidencias/README.md) cuando haya comprobaciones nuevas, manteniendo la fecha y los límites de cada resultado. Las reglas se aplican también a futuras subcarpetas y fechas.

El empaquetador excluye esos archivos y la auditoría rechaza su incorporación forzada a Git o a los activos declarados. Antes de hacer commit, comprobar lo preparado con `git diff --cached --stat` y ejecutar `python Herramientas/Reproducibilidad/verificar_publicacion.py` en el checkout. Añadir un patrón a `.gitignore` no retira archivos ya versionados: si corresponde, usar `git rm --cached` sobre las rutas concretas y conservar los originales locales.
