# Walmart Visión · aplicación del equipo

La app del equipo permite comprobar detecciones, registrar incidencias por foto, nivel o zona, y comparar ejecuciones. **Descargar lote** guarda las fotos, resultados y marcas en un ZIP que se puede recuperar con **Abrir lote de revisión**. Las fotos de la sesión se procesan localmente y las marcas quedan en el navegador o en el lote exportado. [Guía de revisión](Documentacion/REVISION_EQUIPO.md).

## Abrir la app

En Windows x64, extrae el [MVP publicado](../Entregables/README.md) y abre **iniciar_equipo.cmd**. Si trabajas en un clon, usa [iniciar.cmd](iniciar.cmd). Abre **http://127.0.0.1:8095** o la dirección que indique la consola. La preparación inicial requiere Internet. [Docker para el equipo](DOCKER.md).

## Analizar e interpretar

- Carga hasta 50 fotos JPG, PNG o WebP, de hasta 10 MB y 24 megapíxeles cada una y 500 MB en total. Puedes revisar las fotos terminadas mientras sigue el análisis.
- El peso oficial es **V3-cierre-revisado-20261110**. La confianza de detección comienza en **0,60** y se puede ajustar desde **0,25**. [Manifiesto y hashes](modelos.json) · [Ficha del modelo](../Documentacion/Modelo_V3_actual.md).
- **Línea A v2.2** es la opción predeterminada. Usa un índice visual de 0 a 100, con umbral 52 y una regla de huecos. En Ajustes de análisis puedes elegir **Basal · experimental** o **Ambos**. [Qué significa cada alerta](../Documentacion/Usar_Walmart_Vision.md#interpretar-los-resultados) · [Comparar con Basal](Documentacion/COMPARACION_BASAL_20261112.md).
- El filtro de calidad y el detector de personas pueden marcar una foto como no evaluable. Un borde recortado o un superior abierto con geometría dudosa pueden requerir revisión. Revisa visualmente carros y otros obstáculos. [Recorrido del código](Documentacion/LEER_CODIGO.md).

Para consulta de alertas, historial compartido y reportes CSV, Excel o PDF, abre la [app cliente](../Aplicacion_Cliente/README.md) en 8098.

## Desarrollar desde un clon

El repositorio incluye el manifiesto, el peso oficial y el preparador de Windows. Clona el proyecto y abre `Aplicacion/iniciar.cmd` en Windows, o ejecuta `docker compose up --build -d --wait` desde `Aplicacion` para usar Docker. La primera preparación requiere Internet. El código de main puede ser más reciente que el ZIP de la release.

El mapa de evidencia de Línea A se muestra en fucsia. Tras modificar los módulos incluidos en `edge_sources`, actualiza sus SHA-256 en `modelos.json` para que la aplicación pueda verificar su integridad.

Para comprobar el código y construir paquetes desde un clon, consulta [Distribución y pruebas](../Distribucion/README.md). No se necesita el laboratorio interno.

Si el peso o el estimador cambian, vuelve a analizar las fotos guardadas para ver la lectura vigente.

## Licencia

Código original del equipo: [AGPL-3.0-only](../LICENSE). Consulta [licencias y procedencia de datos/pesos](../LICENCIAS.md) y [avisos de terceros](../NOTICE.md). Los datos no reciben una licencia pública por este acuerdo sobre el código.
