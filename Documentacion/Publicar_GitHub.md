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

## Compartir las imágenes de demostración desde Drive

Se preparó una selección confirmada de **tres fotos reales y tres variantes sintéticas**, documentada en [Imágenes para probar Visión](Imagenes_de_prueba.md). Es una excepción limitada a esas seis imágenes; el dataset completo sigue distribuyéndose por separado. El ZIP de la aplicación publicado conserva su contenido.

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

Publicar código, pruebas, guías vigentes y resúmenes de resultados que respalden el proyecto. El material obligatorio de `Fase 1/` se conserva en Git. Las guías de versiones anteriores mantienen sus rutas y llevan un aviso histórico, con un enlace a la documentación vigente; consultar el [índice histórico](Historico.md).

Los respaldos `Datos/Registros/Particiones/**/respaldo_registros/`, los logs bajo `Documentacion/Evidencias/` y las respuestas completas `consulta_github_*.json` de esa carpeta quedan solo en local. Actualizar los [resúmenes públicos](Evidencias/README.md) cuando haya comprobaciones nuevas, manteniendo la fecha y los límites de cada resultado. Las reglas se aplican también a futuras subcarpetas y fechas.

El empaquetador excluye esos archivos y la auditoría rechaza su incorporación forzada a Git o a los activos declarados. Antes de hacer commit, comprobar lo preparado con `git diff --cached --stat` y ejecutar `python Herramientas/Reproducibilidad/verificar_publicacion.py` en el checkout. Añadir un patrón a `.gitignore` no retira archivos ya versionados: si corresponde, usar `git rm --cached` sobre las rutas concretas y conservar los originales locales.
