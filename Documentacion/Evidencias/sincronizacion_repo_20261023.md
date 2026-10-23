# Verificación de fuentes para actualizar el repositorio, 23/10/2026

La preparación incorpora el orden de carpetas y registros, las 458 imágenes V3 mediante sus metadatos, la partición 327/68/63, las correcciones de anotación documentadas y los cambios recientes del visor y laboratorio. V3 conserva su entrenamiento deshabilitado.

Se incorporó primero la actualización remota de `main` hasta `2c68440`. Los cambios locales anteriores se respaldaron con su parche, sus archivos y un stash identificado antes de sincronizar. Las muestras de voz y el piloto retirado conservan su respaldo local; no se incorporan como datos activos o entregables nuevos.

## Comprobaciones

- **Reproducción y publicación:** 17 pruebas correctas, incluidas las del complemento de activos locales y la prohibición de reemplazar paquetes publicados.
- **Visor:** 28 pruebas correctas, ejecutadas en un proceso separado del preparador para evitar colisiones de nombres de módulos.
- **Datos:** 14 pruebas correctas desde el checkout preparado.
- **Laboratorio:** 250 casos descubiertos. Pasaron 247 inicialmente; dos fallaron por depender de una carpeta temporal inexistente y pasaron tras corregir su preparación. Uno se omite mediante `RUN_NIVELES_REAL`, porque la integración real es opcional. Resultado combinado: 249 correctos y una omisión; no se ejecutó un entrenamiento real.
- **Auditoría de publicación:** comprueba sintaxis, enlaces disponibles o activos declarados, ausencia de credenciales en JSON y exclusión de temporales, fotos de datos, pesos y ZIP grandes.
- **CI:** se añadió la suite de mantenimiento de datos a las comprobaciones existentes de reproducción y visor.

## Activos separados del código

El [manifiesto complementario](../../reproducibilidad/activos_locales_20261023.json) declara 401 recursos locales y los ZIP de Visión conservados, con archivos, tamaños y SHA-256 reales. Los recursos se prepararon en `Walmart_Recursos_V3_20261023.zip`, para distribución al equipo mediante `--assets`. No se añadieron URLs ficticias ni se sustituyó el manifiesto de la release anterior. Publicar estas fuentes no publica una release ni los activos privados.

Los respaldos, logs completos y recibos de Git se conservan en `.resguardo/actualizacion_repo_20261023/` del laboratorio.
