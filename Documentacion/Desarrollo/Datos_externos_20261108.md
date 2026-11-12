# Migración de datasets a almacenamiento externo · 8 de noviembre de 2026

Estado: **completado**. Se verificaron Windows, Docker, integridad, respaldos y servicios antes de retirar las copias seleccionadas de C:. El estado estructurado (`Datos/Registros/Almacenamiento/estado_actual.json`, archivo del entorno local; fuera de esta distribución) y el recibo local `retiro.json` registran el cierre.

**Espacio observado en C:** de 14,966 a 26,154 GiB libres, un aumento de **11,188 GiB** entre mediciones. La diferencia incorpora el respaldo conservado y los archivos de control; otros procesos del equipo pueden modificar el espacio. No se presenta el volumen lógico trasladado como ahorro físico.

## Organización aplicada

El inventario inicial registró 15.780 archivos físicos: 12.976 en los cuatro bloques seleccionados de C: y 2.804 en E:. No se recorrieron junctions, dependencias externas ni el worktree de publicación. Se verificaron los hashes actuales de las 609 fuentes y sus copias clasificadas.

E: conserva las fuentes por local y lote en `Fuentes/`, las variantes y sus controles en `Derivados/Ocupacion_20261106/`, la colección práctica en `Pruebas_ocupacion/`, y las imágenes de revisión en `Revision/`. Los índices originales se guardan en `Catalogo/Originales_20261106/`, con evidencia anterior adicional en `Catalogo/Evidencia_previa_20261108/`. Los nombres anteriores mantienen compatibilidad mediante referencias registradas.

Las 609 copias clasificadas se consolidaron como enlaces duros a sus fuentes exactas. Conservan los nombres y la distinción histórica de uso, sin crear otra asignación train/val. Son el mismo archivo físico que su fuente: no deben editarse para generar variantes. La colección práctica de 281 PNG permanece disponible. Los controles originales y el lote incompleto de 281 variantes disponibles y 424 pendientes no cambian de estado.

## Selección de C: y respaldo

Se seleccionaron 16 carpetas exclusivamente de imágenes de datasets: 3.847 archivos, **18.530.794.985 bytes lógicos (17,258 GiB)**. Se copiaron y verificaron primero las exportaciones históricas, luego el dataset del ensayo oficial y finalmente la preparación activa. Los destinos y correspondencias exactos están en el manifiesto local y en el catálogo portable.

Las fuentes compartidas, las carpetas mixtas con evidencia y las ilustraciones fuera de esta selección permanecen en C:. Cuando un archivo exportado carecía de otra copia independiente conservada, se creó una copia por contenido en `.resguardo/Almacenamiento_20261108/`: **6.272.246.433 bytes (5,841 GiB)**. El retiro no elimina la última copia independiente de esos bytes. Esto conserva datos únicos en C: además de E: y reduce el ahorro respecto del volumen lógico externalizado.

El respaldo es local, en los dos volúmenes disponibles. No se declara protección ante pérdida simultánea ni respaldo remoto. No se reconstruyeron checkpoints ni respaldos retirados anteriormente. Fase 1/Fase 2, el entorno y la publicación conservan sus ubicaciones.

## Acceso portable

El catálogo (`Datos/Registros/Almacenamiento/catalogo.json`, archivo del entorno local; fuera de esta distribución) usa referencias lógicas completas y destinos relativos, tamaño y SHA-256. La raíz real se toma de `WALMART_DATA_ROOT` o de `.config-modelo/almacenamiento.local.json`. Los lectores adaptados resuelven archivos registrados y las rutas históricas mantienen sus identificadores.

El panel solo expone los archivos expresamente autorizados; la configuración no permite leer cualquier ruta del disco externo. Los lectores de preparación, exportación, comprobación del entrenador y ocupación usan la resolución común. Las herramientas de pruebas dejan de depender de una letra de unidad fija. Los índices congelados con rutas absolutas usan correspondencias exactas, conservando sus bytes originales.

Los alias de las 16 carpetas conservan compatibilidad en Windows. Docker monta `/datasets` y cada ubicación lógica en lectura mediante `compose.modelos.datos.yml`, conservando los montajes históricos. Las salidas nuevas permanecen en los montajes operativos de C: con escritura. El iniciador del panel añade la configuración externa automáticamente. Se corrigió la conservación del identificador lógico del inventario histórico cuando Docker representa un alias de Windows mediante `/mnt/host`.

[Configuración, reconexión y recuperación](../../Datos/Registros/Almacenamiento/README.md).

## Identidad y límites conservados

Las 21 entradas no identificadas por el CSV del 6/11 se encontraron en C: por contenido y tienen un destino externo en las exportaciones, sin inferir equivalencia por nombre. Los 275 registros de la partición, sus 11 bloqueos, escenas y familias permanecen fijados. La exportación habilitada conserva 171 train, 59 validación real y 34 sintéticas. Se comprueban las fuentes y las rutas `serve_path` de los 163 registros de ocupación sin cambiar sus etiquetas.

Las tres fuentes V1 retiradas por Vicente se registran como ausencias conocidas, sin hashes inventados ni restauración. El verificador global conserva esa incidencia; esta operación no es una auditoría global aprobada. R254 sigue excluida y la reserva final no se usa para inferencia, ajuste ni selección.

La app y el paquete aislado del 8/11 se probaron sobre `lider_express_014_A_vacios.png`, con lecturas de E: prohibidas: ambos devuelven seis niveles con Línea A, revisión `linea_a_20261108_contornos_conservados` y umbral 52. Este smoke comprueba autonomía y funcionamiento; no es una evaluación de precisión. No se cambiaron pesos, estimador, umbrales ni resultados históricos. La release del 5/11 conserva su estimador anterior y no se volvió a publicar.

## Recibos y reversión

El retiro terminó con 3.847 archivos y 16 carpetas comprobadas; no quedan sus carpetas temporales `.antes_externo`. Cada referencia original apunta al destino externo registrado y conserva su identidad. Las 21 correspondencias pendientes del CSV están cerradas en cobertura_final.json (`Datos/Registros/Almacenamiento/cobertura_final.json`, archivo del entorno local; fuera de esta distribución).

La comprobación previa al retiro verificó los 3.847 archivos y 1.138 hashes únicos, todas las fuentes y metadatos conservados de los bloques inventariados, las rutas de ocupación y las copias independientes. En Docker se comprobaron la partición, la exportación activa, el ensayo congelado, una referencia histórica, una exportación compartida y la configuración del siguiente refuerzo, sin iniciarlo. Pasaron las suites de modelos/rutas (79), ocupación (14), inventario (43), la regresión del alias de Docker y las pruebas finales del panel (15); varias suites se solapan y no se suman como casos distintos. Los catálogos actual e histórico, la salud del laboratorio y el catálogo de la app respondieron HTTP 200 tras el reinicio.

La verificación global de estructura conserva además un enlace previo de `README.md` a `Fase 1/`, ausente en la raíz al iniciar esta tarea. No se reconstruyó material académico ni se alteraron sus ubicaciones por esta migración. Esta incidencia y las tres fuentes V1 ausentes impiden presentar el resultado como una auditoría global aprobada.

La carpeta local [Almacenamiento](../../Datos/Registros/Almacenamiento/README.md) contiene inventario, manifiesto por archivo, organización de E:, copias verificadas, activación, comprobaciones y retiro. Los textos previos se conservaron en `antes/`. El catálogo y sus controles permiten comprobar identidades al conectar otro equipo.

E: conserva otra copia verificada de los índices y recibos en `Catalogo/Migracion_20261108/`. No se sincronizó el worktree de publicación, no se publicó ninguna release y no se modificaron CVAT, particiones, etiquetas, modelos ni el ZIP oficial.

Antes del retiro, cada origen se mantiene como carpeta física temporal `.antes_externo`; después se retiran exclusivamente los archivos del manifiesto con destino y copia independiente verificados. Nunca se borra recursivamente un alias. Un lote con incidencia debe conservar sus originales.

Después del retiro, revertir requiere copiar desde el destino verificado o desde `recuperacion_c`, retirar solo el alias y restaurar los montajes afectados. Cambiar una variable no reconstruye los archivos de C:. No aplicar esa recuperación a ausencias intencionales ni a material retirado en operaciones previas.

[Plan original](Plan_datos_externos_20261108.md) · [Limpieza anterior](Limpieza_orden_20261108.md) · [Mapa del proyecto](Mapa_del_proyecto.md).
