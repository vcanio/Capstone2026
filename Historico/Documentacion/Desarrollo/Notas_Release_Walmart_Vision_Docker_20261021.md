> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Walmart Visión · Docker para macOS · 21 de octubre de 2026

Walmart Visión incorpora ejecución local con Docker para Mac Intel y Apple Silicon. El paquete conserva los cuatro modelos V1/V2, la interfaz de análisis de fotografías y los métodos Solo YOLO y YOLO + detección de bordes. El análisis utiliza CPU y las fotografías se procesan en memoria en el computador.

## Descargar e iniciar

Descargar **Walmart_Vision_Docker_20261021.zip**, extraerlo por completo y abrir Terminal en la carpeta `Walmart_Vision`, donde está `compose.yaml`. Con Docker Desktop instalado y abierto, ejecutar:

```bash
docker compose up --build -d --wait
```

Abrir http://localhost:8095. La primera construcción requiere Internet para descargar la imagen base y las dependencias. Para detener la aplicación, ejecutar `docker compose down`. La guía `DOCKER.md`, incluida en el ZIP, explica el reinicio sin descarga ni construcción, el cambio de puerto y la solución de problemas. El paquete también conserva el iniciador de Windows y el cuaderno de Colab.

## Integridad

- Archivo: `Walmart_Vision_Docker_20261021.zip`.
- Tamaño: 37 480 056 bytes.
- SHA-256: `4af7fc6ca6fbd48f9fbfef938c796e98710e787c335b6713d587ce514a93f259`.
- Archivo de comprobación: `Walmart_Vision_Docker_20261021.sha256`.

En Terminal de macOS se puede comprobar con `shasum -a 256 Walmart_Vision_Docker_20261021.zip` y comparar el resultado con el hash anterior.

Los archivos automáticos «Source code» de GitHub contienen el código del repositorio. Para usar la aplicación con los cuatro pesos incluidos, descargar el ZIP con el nombre indicado arriba. Esta versión se distribuye como un activo nuevo; la entrega del 20 de octubre conserva su contenido.

## Verificación y límites

Pasaron 21 pruebas automatizadas: 16 de inferencia/HTTP y 5 de transiciones de interfaz. Se construyeron imágenes Linux AMD64 y ARM64 y se ejecutaron 16 predicciones HTTP con la red externa deshabilitada: cuatro modelos con ambos métodos en cada arquitectura. Se verificaron las imágenes devueltas, la conservación de estados y confianzas YOLO entre métodos y los hashes de los pesos y módulos de bordes. Además, se comprobó Compose en AMD64 con dos puertos y dos predicciones desde el anfitrión.

Las pruebas se ejecutaron en Docker Desktop sobre Windows con motor Linux; ARM64 utilizó emulación. La prueba en un Mac físico sigue pendiente. Los tiempos de emulación no representan el rendimiento de un Mac. El [registro Docker](https://github.com/vcanio/Capstone2026/blob/main/Aplicacion/VERIFICACION_DOCKER.md) conserva el alcance y las incidencias observadas.

El modelo puede omitir niveles o asignarles un estado incorrecto. V2 base distingue `reponer` y `suficiente`; no reconoce `no_evaluable`. La señal de bordes es experimental y no equivale a un porcentaje validado de producto. Este paquete no incluye fotografías ni datos de entrenamiento o evaluación.
