# Laboratorio de desarrollo: instalación y repetición de ensayos

Esta guía está dirigida al **equipo de desarrollo**. La entrega para el usuario es Walmart Visión: para descargarla, analizar fotos e interpretar resultados, seguir la [guía de uso](../Usar_Walmart_Vision.md). No requiere el panel de entrenamiento, CVAT ni los paquetes del laboratorio.

La [guía conceptual](../../Historico/Documentacion/Guia_conceptual_V1_V2.md#cómo-se-relacionan-las-tres-interfaces) explica cómo se construyó el sistema sin necesidad de instalar esas herramientas. Los pasos siguientes se conservan para continuar el desarrollo o repetir ensayos con los activos correspondientes; la Release pública no distribuye un laboratorio completo ni el dataset.

La aplicación descargable es `walmart-vision-2026-10-22`. Los paquetes del laboratorio conservan la versión `avance-2026-10-20`. El código y el manifiesto se guardan
en Git. La Release pública contiene únicamente Walmart Visión con sus modelos y
bordes. Los paquetes del laboratorio se transfieren por separado para desarrollo
y se instalan con --assets; no se publican como adjuntos de esa Release.

Para compartir mejoras entre Paulo, Vicente Canio y Vicente Vilches, seguir la
[guía de trabajo en equipo](Trabajo_en_equipo.md), también disponible en
[PDF](Trabajo_en_equipo.pdf). Incluye dónde guardar scripts, abrir PR y descargar
los cambios integrados por los demás.

## Antes de empezar

Para familiarizarse con el proyecto, leer la [guía de conceptos y ejemplos](../Guia_para_entender_el_proyecto.md). Entrenar significa ajustar un modelo con imágenes etiquetadas; ejecutar o hacer inferencia significa utilizar un modelo ya entrenado. Walmart Visión permite lo segundo sin preparar el entorno de entrenamiento.

Los comandos se ejecutan desde la carpeta del repositorio. Las rutas como `D:/Transferencias/Walmart` son ejemplos y deben reemplazarse por la carpeta real donde se recibieron los ZIP. Un hash es una huella que permite comprobar si un archivo cambió.

## Elegir el alcance

| Necesidad | Archivos y entorno |
|---|---|
| Probar fotografías propias | Walmart_Vision_Ocupacion_20261022.zip. Iniciador Windows x64 o Docker Desktop en Mac Intel/Apple Silicon; Internet en la preparación inicial; sin CVAT. |
| Comprender la anotación y el entrenamiento | Guía conceptual, arquitectura, guías de anotación y mapa del código; no requiere instalar el laboratorio. |
| Desarrollar, evaluar o entrenar | Clon + datos_fuentes + datos_exportados + modelos_resultados; Python 3.11/3.12 para preparar y Docker para ejecutar. |
| Revisar el informe | Paquete informe; no requiere modelos ni datos de entrenamiento. |
| Anotar nuevas fotografías | Cuenta propia y acceso al CVAT compartido, configurado por separado. |

## Demo portátil

El recorrido para el usuario, incluida la comprobación pendiente en otro computador, está en [Usar Walmart Visión](../Usar_Walmart_Vision.md). Como resumen, descargar Walmart_Vision_Ocupacion_20261022.zip de la [Release](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-2026-10-22), extraer todo y, en Windows, ejecutar
`Walmart_Vision/iniciar.cmd`. El primer inicio prepara un Python privado con sus
dependencias. Seleccionar V1 o V2 en el paso 0, después un modelo, elegir
YOLO + detección de bordes o Solo YOLO y subir una foto. El modo con bordes añade
mapas de señal y bordes sin cambiar los estados YOLO.

En Mac, abrir Docker Desktop y seguir la [guía Docker](../../Aplicacion/DOCKER.md) incluida en ese mismo paquete.

V1 devuelve vacío, baja, suficiente y no evaluable. V2 base devuelve reponer y
suficiente: no reconoce no evaluable. Una fotografía sin referencias no permite
calcular precisión. No se guardan las fotos subidas a la demo.

## Instalar el laboratorio desde una copia nueva

Instalar Git, Python 3.11 o 3.12 y Docker con contenedores Linux. En Windows se usa
Docker Desktop con WSL2. Empezar por CPU; NVIDIA es opcional.

```powershell
git clone https://github.com/vcanio/Capstone2026.git
cd Capstone2026
python Laboratorio/Reproducibilidad/preparar.py --assets D:/Transferencias/Walmart
```

Los paquetes se entregan mediante coordinación interna del equipo; este repositorio no ofrece un canal público de solicitud ni descarga para ellos. Para seguir los comandos de preparación de esta guía, acordar con el mantenedor la entrega de `datos_fuentes`, `datos_exportados`, `modelos_resultados` e `informe`: el preparador incluye esos cuatro paquetes por defecto. Sin los datos y modelos se puede leer el código y usar Visión, pero no repetir los ensayos conservados.

El preparador
lee los ZIP locales y verifica las fuentes, las exportaciones inmutables, los
pesos/resultados y el informe. Mantiene rutas, etiquetas y particiones. Repetirlo no duplica ni
sobrescribe archivos diferentes. Se necesitan varios GB de almacenamiento para
los activos, su extracción y las imágenes Docker.

Usar la carpeta que contiene los ZIP recibidos por transferencia separada:

```powershell
python Laboratorio/Reproducibilidad/preparar.py --assets D:/Transferencias/Walmart
```

Para incorporar la demo o recuperar por separado el informe:

```powershell
python Laboratorio/Reproducibilidad/preparar.py --paquetes demo
python Laboratorio/Reproducibilidad/preparar.py --assets D:/Transferencias/Walmart --paquetes informe
```

La demo se extrae en `Entregables/Walmart_Vision/`. Para comprobar los archivos ya
instalados, sin descargar ni escribir:

```powershell
python Laboratorio/Reproducibilidad/preparar.py --verificar
python Laboratorio/verificar_proyecto.py
python Laboratorio/Datos/particionar_lider_express.py --verify
```

## Iniciar en CPU

En Windows, desde PowerShell:

```powershell
& ./Herramientas/Modelos/iniciar_panel.ps1 -Cpu -Build
```

En Linux, o usando Docker directamente:

```bash
docker compose -f Infraestructura/Docker/compose.modelos.yml up -d --build --wait
```

Abrir http://localhost:8090. El Compose base no monta contraseñas ni necesita CVAT.
Para GPU NVIDIA, iniciar el script sin -Cpu, o añadir compose.modelos.gpu.yml a la
orden Docker. Requiere driver y acceso de GPU desde Docker; no es necesario para
probar la instalación en CPU.

**Ejemplo de comprobación:** elegir V2 y v2_base_yolo26n_01, cargar
lider_express_040_0_original.jpg y analizar con confianza 0,25 y NMS 0,70.
La confianza filtra predicciones según su puntuación; NMS reduce las muy superpuestas. Estos valores permiten comparar con la evaluación conservada, que contiene cinco niveles: cuatro suficientes y uno reponer.
Comparar con el primer caso del informe. Los números de detección del visor pueden
variar respecto de comparaciones históricas.

## Repetir entrenamiento sin CVAT

Primero comprobar el ensayo conservado:

```bash
docker compose -f Infraestructura/Docker/compose.modelos.yml exec panel_modelos python Laboratorio/Reproducibilidad/repetir_ensayo.py --ensayo v2_base_yolo26n_01_20261020_004933_b105 --solo-verificar
```

Después entrenar en una carpeta nueva con la misma configuración:

```bash
docker compose -f Infraestructura/Docker/compose.modelos.yml exec panel_modelos python Laboratorio/Reproducibilidad/repetir_ensayo.py --ensayo v2_base_yolo26n_01_20261020_004933_b105 --nombre replica_yolo26_equipo --device cpu
```

Usar --device auto en un contenedor con GPU disponible. Los cuatro IDs originales
están en [Experimentos](../../Laboratorio/Experimentos/README.md). La ejecución CPU puede tardar
considerablemente más que GPU. --epochs 1 permite comprobar el recorrido, pero
ese ensayo corto no reproduce las métricas del entrenamiento completo.

El script verifica la exportación y las huellas de snapshot/partición antes de
entrenar. Solo evalúa train/val; no consulta CVAT ni la reserva final. No garantiza
pesos idénticos bit a bit entre hardware/controladores diferentes. Conservar el
entorno y comparar métricas, clases y denominadores, además de la semilla.

Para entrenamiento de tres estados con nuevos datos aprobados, usar
[entrenar_niveles.py](../../Historico/Documentacion/Desarrollo/Entrenamiento_niveles_v2.md). V2 base de dos clases se reproduce
con repetir_ensayo.py o desde el panel, sin fingir una tercera clase ausente.

## Conectar CVAT de forma opcional

Solicitar al responsable la URL y una cuenta personal. Copiar
Infraestructura/Docker/acceso_cvat.example.json a
Infraestructura/CVAT/acceso_local.json y completar las credenciales localmente.
Ese destino está ignorado por Git. Copiar .env.modelos.example a .env.modelos y
configurar MODEL_CVAT_URL con su terminación /api; para HTTPS remoto dejar
MODEL_CVAT_HOST_HEADER vacío.

```powershell
& ./Herramientas/Modelos/iniciar_panel.ps1 -Cpu -ConCvat
```

En Linux añadir compose.modelos.cvat.yml después del Compose base y pasar
--env-file Infraestructura/Docker/.env.modelos. No se distribuye la base de datos
privada de CVAT. Los snapshots/exportaciones bastan para repetir los ensayos.

## Trabajo en equipo

Crear una rama por cambio de código y usar pull requests. Cada entrenamiento debe
tener un nombre nuevo que identifique al autor; no reemplazar los cuatro ensayos
de referencia. Compartir los nuevos pesos como activos y sus métricas/configuración
en Git. Una modificación de etiquetas requiere otra versión; no editar una copia
congelada conservando sus hashes anteriores. Las familias originales y sus variantes
deben conservar el mismo destino. La reserva final no se usa para escoger umbrales.

## Fallos habituales

| Síntoma | Acción |
|---|---|
| Descarga 404 de la demo | Comprobar que se accede a la Release y al ZIP con el nombre indicado; si el activo no está disponible, informar al mantenedor. Los paquetes internos del laboratorio no sustituyen la descarga de Visión. |
| Falta archivo o hash distinto | Repetir preparación en una copia limpia; no reemplazar trabajo modificado a mano. |
| Docker no conecta | Iniciar el motor Docker y comprobar docker version. |
| Error de NVIDIA | Comenzar con -Cpu; verificar compatibilidad de driver y contenedor antes de activar GPU. |
| CVAT deshabilitado | Solo afecta traer anotaciones; usar -ConCvat y configurar acceso personal. |
| No aparecen modelos | Falta instalar modelos_resultados o cambió la estructura de carpetas. |
