# Orden y limpieza del proyecto, 23/10/2026

Operación local solicitada por el usuario. El objetivo fue distinguir el visor V2 disponible, el trabajo de datos V3 y los antecedentes, corregir referencias y limpiar material regenerable sin alterar datos o ensayos.

## Cambios

- README principal y guías de entrada actualizados con V3: 458 imágenes, una clase `Nivel` y partición 327/68/63. El catálogo completo conserva 567 imágenes únicas de todas las etapas.
- [Mapa del proyecto](../Desarrollo/Mapa_del_proyecto.md) e [índice de entregables](../../Entregables/README.md) incorporados.
- Corregidos los enlaces a contactos ausentes de Líder 2; ahora se usa el catálogo verificado de escenas. La copia duplicada de la guía del lote D se sustituyó por referencias a las guías canónicas.
- Preparado `Walmart_Vision_Actual_20261023.zip`: dos modelos V2, instrucciones coherentes y fecha nueva. La entrega del 22/10 conserva sus bytes. Se comprobaron ZIP, SHA-256, pesos y sintaxis de celdas Python; la directiva `%pip` se trata como instrucción de IPython. No se ejecutó una sesión remota de Colab.
- Las diferencias entre ambos ZIP se limitan a instrucciones, documentación Docker, fecha del manifiesto, nombre de paquete en el cuaderno y nota de verificación. Pesos, interfaz e inferencia permanecen idénticos.

## Limpieza y conservación

Se archivaron **1.592 archivos auxiliares**, **1.166.110.896 bytes**, en `.resguardo/orden_proyecto_20261023/temporales_anteriores/`, conservando hashes. Archivar dentro del mismo disco no equivale a liberar ese espacio.

Se eliminaron **3.801 archivos regenerables**, **278.648.974 bytes**: bibliotecas temporales de video y cachés Python acotadas. Se retiró la carpeta raíz `tmp/`, que estaba vacía. La carpeta `.tmp/` conserva las entradas del generador de video, extracciones locales identificadas y el antecedente de visibilidad cuyo `node_modules` enlaza dependencias compartidas externas. El enlace y su destino se conservaron.

Se verificó la conservación de **452 archivos protegidos** de datos, anotaciones, pesos, manifiestos y entregas anteriores. El checkout `.publicacion/repositorio` conserva su HEAD y sus **33 entradas de cambios previos**. No hubo escrituras en CVAT, entrenamiento, commit, push ni publicación.

Los entornos instalados, paquetes del laboratorio, fotos originales, variantes, reservas y exportaciones usadas por los ensayos permanecen en sus ubicaciones. Los documentos y programas editados tienen respaldo previo en `.resguardo/orden_proyecto_20261023/documentos_y_codigo_previos/`.

## Comprobaciones

El verificador general comprueba enlaces locales, catálogo de seis lotes, dos exportaciones compartidas y sintaxis Python. Las **14 pruebas de mantenimiento de datos** pasaron. Los verificadores V2 y V3 comprueban sus particiones por separado. El [resumen de verificación](orden_proyecto_20261023.json) registra los resultados finales, sin convertirlos en una evaluación del modelo ni una prueba nueva de Windows, macOS o Colab.

Recibos locales: `limpieza.json`, `proteccion.json`, `verificacion_limpieza.json` y `paquete_20261023.json` dentro de `.resguardo/orden_proyecto_20261023/`.
