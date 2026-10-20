# Publicar la demo de Walmart Lite

La Release pública `avance-2026-10-20` sirve solo para probar los modelos con
fotografías propias. Debe contener **un único activo**:
`Walmart_Lite_V2_Deteccion_Bordes_20261020.zip`. Incluye la interfaz, los cuatro pesos y la
revisión 2 de detección de bordes. No adjuntar datos, informes ni paquetes de desarrollo.

## Código y commit

El checkout preparado está en `.publicacion/repositorio/`. Revisar sus cambios,
hacer commit y push a main antes de publicar el borrador. El empaquetador no hace
commit, push ni modifica credenciales. No usar push forzado.

```powershell
Set-Location .publicacion/repositorio
git status --short
git diff --cached --stat
git commit -m "Integra bordes en Lite y simplifica la Release"
git push origin main
```

## Revisar el borrador y publicar

1. Abrir Releases en https://github.com/vcanio/Capstone2026 y editar el borrador
   con tag avance-2026-10-20, Target main.
2. Usar el título **Walmart Lite V2 + detección de bordes** y la
   [descripción preparada](Notas_Release_avance_20261020.md).
3. En Assets conservar solo Walmart_Lite_V2_Deteccion_Bordes_20261020.zip. El ZIP local
   preparado está en `.publicacion/releases/`. Esperar a que termine la carga.
4. Mantener **This is a pre-release** por su carácter experimental y publicar.
5. Descargar el ZIP publicado, extraerlo en una carpeta nueva y ejecutar
   Walmart_Lite/iniciar.cmd. Probar una fotografía con cada método.

Los archivos Source code automáticos que añade GitHub son normales. No contienen
los pesos y no sustituyen el ZIP portátil. No volver a utilizar el nombre del ZIP
anterior con otro contenido; esta revisión tiene un nombre nuevo.

## Paquetes del laboratorio, fuera de la Release

Los cuatro paquetes de datos, exportaciones, modelos/resultados e informe se
conservan en `.publicacion/paquetes_desarrollo/`, junto con metadatos de integridad
y copias históricas. Compartirlos por separado con los compañeros que desarrollan.
No forman parte de la descarga para probar la app. El
[preparador](Replicar_proyecto.md) los instala con --assets RUTA_A_LOS_ZIP.

Para regenerar la demo y actualizar el checkout desde el laboratorio:

```powershell
python Herramientas/Modelos/empaquetar_demo_lite.py --perfil v2
python Herramientas/Reproducibilidad/empaquetar_publicacion.py --solo-codigo
```

La regeneración completa de paquetes coloca los del laboratorio en
paquetes_desarrollo y solo la demo en releases. Los pesos, ZIP, .env, accesos
personales, entornos y fotos privadas siguen fuera del historial Git.
