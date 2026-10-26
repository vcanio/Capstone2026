> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../Modelos/Actual/README.md).

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

La primera ejecución de GitHub detectó que el paso nuevo necesitaba Shapely y que la comprobación de metadatos todavía exigía fotos locales incluso con `verify_images=False`. Se añadió la dependencia de geometría y se separó ese modo de la verificación completa. El modo predeterminado sigue exigiendo imágenes y hashes, con una prueba nueva que comprueba el rechazo si falta una foto. La suite de datos pasa a 15 casos; no se descargan ni publican fotos privadas para ejecutar CI.

## Activos separados del código

El [manifiesto complementario](../../Historico/Reproducibilidad/activos_locales_20261023.json) declara 401 recursos locales y los ZIP de Visión conservados, con archivos, tamaños y SHA-256 reales. Los recursos se prepararon en `Walmart_Recursos_V3_20261023.zip`, para distribución al equipo mediante `--assets`. No se añadieron URLs ficticias ni se sustituyó el manifiesto de la release anterior. Publicar estas fuentes no publica una release ni los activos privados.

Los respaldos, logs completos y recibos de Git se conservan en `.resguardo/actualizacion_repo_20261023/` del laboratorio.
