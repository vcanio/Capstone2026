# Publicar el código y los activos de la entrega

La preparación no hace commit, tag, push ni carga archivos a GitHub. El checkout
revisable está en `.publicacion/repositorio/` del laboratorio y los activos en
`.publicacion/releases/`. Conserva el historial remoto y las entregas de Fase 1.

## Revisar y publicar el código

En PowerShell, desde la raíz del laboratorio:

```powershell
Set-Location .publicacion/repositorio
git status --short
git diff -- README.md
python Herramientas/Reproducibilidad/verificar_publicacion.py
git add .
git diff --cached --stat
git diff --cached --check
git commit -m "Prepara laboratorio V1 V2 reproducible y entrega intermedia"
git push origin main
```

Si main cambió desde la clonación, resolver primero esa diferencia en el checkout;
no usar push forzado. Los archivos nuevos aparecen en el diff después de git add.
No se ha cambiado la identidad de Git ni sus credenciales.

## Publicar los archivos grandes

En GitHub, abrir Releases y crear una nueva Release con tag
`avance-2026-10-20`, apuntando al commit anterior. Título sugerido:
“Avance intermedio y laboratorio reproducible V1 V2”.

Adjuntar TODOS los archivos de `.publicacion/releases/`:

| Archivo | Contenido |
|---|---|
| Walmart_Datos_Fuentes_20261020.zip | Imágenes originales/sintéticas y evidencias binarias de los datos. |
| Walmart_Datos_Exportados_20261020.zip | Exportaciones YOLO congeladas, con integridad y etiquetas. |
| Walmart_Modelos_Resultados_20261020.zip | Best.pt, pesos generales, comparaciones y resultados visuales; herramienta uv verificada para regenerar Lite. |
| Walmart_Lite_V2_20261020.zip | Demo autónoma con cuatro modelos V1/V2 base. |
| Walmart_Informe_20261020.zip | PDF, Word y HTML del informe intermedio. |
| artefactos.json | Versión, rutas, tamaños y hashes de los activos. |
| SHA256SUMS.txt | Huellas SHA-256 de todos los archivos distribuidos. |

Los nombres y el tag deben coincidir exactamente con
[artefactos.json](../reproducibilidad/artefactos.json). Si se cambia el contenido de
un ZIP, regenerar manifiesto y sumas antes de publicar. No reemplazar silenciosamente
un activo publicado: crear otra versión y actualizar el manifiesto del código.

El manifiesto y el preparador también admiten transferencia privada de esos ZIP:
los compañeros pueden usar --assets sin esperar la publicación. La Release del
repositorio actual será pública; revisar que esa sea la vía elegida para las imágenes.

## Verificar desde otro equipo

Seguir [Replicar el proyecto](Replicar_proyecto.md) en una carpeta nueva. Confirmar
descarga, integridad, inicio CPU y ejemplo V2. La verificación local de una copia
separada está en [VERIFICACION](../reproducibilidad/VERIFICACION.md); no sustituye la
comprobación de descarga desde GitHub después de publicar los activos.

## Regenerar la preparación desde el laboratorio

```powershell
python Herramientas/Modelos/empaquetar_demo_lite.py --perfil v2
python Herramientas/Reproducibilidad/empaquetar_publicacion.py
```

El segundo comando requiere el checkout ya clonado en .publicacion/repositorio.
Para actualizar solo código/documentación sin reconstruir activos:

```powershell
python Herramientas/Reproducibilidad/empaquetar_publicacion.py --solo-codigo
```

No copiar la carpeta del laboratorio completa a Git. Los .env, accesos privados,
fotos subidas, cachés, entornos, backups, ZIP y pesos se excluyen del historial.
