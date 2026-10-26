> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../Modelos/Actual/README.md).

# Verificación Docker de Walmart Visión · 21 de octubre de 2026

Preparación adicional: `Walmart_Vision_Docker_20261021.zip`, con cuatro modelos, visor, Dockerfile, Compose e instrucciones. Conserva los pesos originales y su manifiesto SHA-256. El activo Windows del 20 de octubre conserva su contenido.

## Comprobaciones

- Las 16 pruebas de inferencia y HTTP de `test_lite.py` pasan en Python 3.12. Incluyen el servidor escuchando en `0.0.0.0`, el acceso desde loopback y el rechazo de Host y Origin externos.
- Las 5 pruebas de transiciones de interfaz de `test_vision_ui.py` pasan sin cambios en el visor.
- Linux AMD64: construcción correcta, `pip check` sin conflictos y comprobación de los hashes de los cuatro modelos al construir.
- Linux AMD64 con `--network none`: 8 predicciones HTTP reales, cuatro modelos con ambos métodos, ejecutadas con UID 10001. Se comprobaron las imágenes devueltas y que los bordes no cambian los estados ni las confianzas YOLO.
- Compose: construcción, arranque saludable, interfaz, lista de cuatro modelos y predicción V2-YOLO26 con bordes desde el anfitrión. Se probaron los puertos 18095 y 18096, publicando solo en `127.0.0.1`, incluido el reinicio con `--pull never --no-build`. Host y Origin externos devuelven HTTP 403. Se retiraron el servicio y la red de prueba.
- Linux ARM64 bajo emulación: construcción correcta, `pip check` sin conflictos, comprobación de hashes y 8 predicciones HTTP reales con `--network none` y UID 10001. Los cuatro modelos terminan con ambos métodos, las imágenes devueltas son válidas y los estados y confianzas YOLO se mantienen entre métodos.

Son 16 predicciones sin red externa entre ambas arquitecturas, más 2 comprobaciones de predicción desde el anfitrión a través de Compose. La imagen base está fijada por el digest multiplataforma `sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`.

La fotografía de comprobación es `lider_express_015_0_original.jpg`, de validación V2, ya identificada en el manifiesto de imágenes de demostración. Se utiliza únicamente para verificar la ejecución; no es una evaluación independiente de precisión ni se incorpora al ZIP.

El paquete comprueba integridad ZIP, cuatro hashes de pesos contra los originales, hashes de módulos de bordes, archivos Docker incluidos con saltos LF, iniciadores Windows con CRLF y sintaxis del cuaderno de Colab. El ZIP Windows publicado conserva su SHA-256 original. Los registros detallados se conservan localmente en `.publicacion/docker_vision_20261021/`.

## Alcance

El entorno de comprobación es Docker Desktop en Windows con motor Linux. ARM64 utiliza emulación. Una construcción o inferencia correcta en ese entorno no acredita una prueba en un Mac físico. La comprobación física en macOS sigue pendiente.

Durante la inferencia ARM64 emulada se observó un aviso de PyTorch sobre `MIDR_EL1` y una sonda de salud HTTP agotó su tiempo durante la carga. Las ocho predicciones terminaron correctamente. Los tiempos de emulación no representan el rendimiento de un Mac; el arranque con Compose y sus sondas se comprobó directamente en AMD64.

Para completarla, registrar macOS, procesador, RAM y versión de Docker Desktop; extraer el paquete en una carpeta nueva; seguir `DOCKER.md`; probar los cuatro modelos con ambos métodos y revisar las cuatro vistas; detener y volver a iniciar sin conexión; registrar incidencias y capturas autorizadas. Registrar Intel y Apple Silicon por separado cuando se disponga de ambos equipos.
