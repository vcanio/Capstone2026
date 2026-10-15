# 🛒 Walmart — Disponibilidad visual en góndolas

Proyecto de Capstone desarrollado para **DUOC UC**, enfocado en aplicar visión por computadora al análisis de disponibilidad visual en góndolas de supermercado.

El prototipo identifica niveles de una góndola en fotografías y los clasifica como **vacío, baja disponibilidad, suficiente o no evaluable**. El objetivo es apoyar la identificación de posibles faltantes mediante imágenes.

## 👥 Integrantes

| Nombre | Correo electrónico |
| :--- | :--- |
| **Vicente Canio** | [vi.canio@duocuc.cl](mailto:vi.canio@duocuc.cl) |
| **Vicente Vilches** | [vi.vilchesm@duocuc.cl](mailto:vi.vilchesm@duocuc.cl) |
| **Paulo Guerra** | [pau.guerra@duocuc.cl](mailto:pau.guerra@duocuc.cl) |

## 🏫 Información académica

- **Institución:** DUOC UC.
- **Docente:** Arturo Vargas.
- **Repositorio:** [github.com/vcanio/Capstone2026](https://github.com/vcanio/Capstone2026).
- **Estado:** prototipo experimental en desarrollo y evaluación.

## 🎯 Objetivo

Desarrollar y evaluar una solución que permita localizar niveles de góndola, estimar su disponibilidad visual y presentar los resultados en una interfaz para facilitar su revisión.

El trabajo incluye la preparación de un dataset propio, la definición de criterios de anotación, el entrenamiento de modelos de segmentación y la comparación de sus resultados.

## 🔎 Estados de disponibilidad

| Estado | Criterio de anotación |
| :--- | :--- |
| **Vacío** | No se observan productos del propio nivel y la visibilidad permite comprobarlo. |
| **Baja disponibilidad** | Hay producto visible, pero ocupa menos del 30 % del ancho completo del nivel. |
| **Suficiente** | El producto visible ocupa al menos el 30 % del ancho completo del nivel. |
| **No evaluable** | La visibilidad u oclusión impide asignar un estado con seguridad. |

Se cuentan los productos visibles al fondo que pertenecen al nivel. El umbral del 30 % es un criterio inicial de anotación pendiente de calibración. La confianza del modelo expresa su puntuación de predicción; el porcentaje de disponibilidad se define por el criterio de anotación.

## ⚙️ Funcionamiento del prototipo

1. **Preparar imágenes:** organizar fotografías reales y variantes sintéticas, separando entrenamiento, validación y reserva final.
2. **Anotar en CVAT:** dibujar polígonos por nivel y asignar su estado conforme a una guía común.
3. **Revisar y entrenar:** importar las anotaciones, comprobar su integridad y registrar la revisión humana antes del entrenamiento.
4. **Evaluar:** comparar localización, clasificación de estados, omisiones y falsas alertas.
5. **Probar fotografías:** analizar una imagen desde el panel y revisar los niveles numerados, estados y contornos generados.

Las fotos subidas para pruebas manuales se guardan separadas y requieren un proceso explícito de preparación y revisión para incorporarse a un dataset.

## 🧰 Tecnologías

| Componente | Tecnología |
| :--- | :--- |
| Procesamiento y lógica | Python, NumPy, OpenCV y Pillow |
| Entrenamiento e inferencia | PyTorch y Ultralytics YOLO |
| Modelos comparados | YOLO11 y YOLO26 con segmentación |
| Anotación | CVAT |
| Interfaz | HTML, CSS y JavaScript |
| Entorno de ejecución | Docker y Docker Compose |

Docker permite empaquetar las dependencias y facilitar la ejecución en otros equipos. Los datos, pesos y configuración de acceso se gestionan por separado.

## 📊 Datos y estado de evaluación

Estado del laboratorio al **15 de octubre de 2026**:

- **Dataset de procedencia:** 102 imágenes propias: 30 reales y 72 sintéticas.
- **Copia revisada usada en ambos ensayos:** 91 imágenes activas después de 11 exclusiones en CVAT.
- **Entrenamiento:** 86 imágenes.
- **Validación:** 5 imágenes reales.
- **Reserva final:** 7 fotografías originales adicionales, separadas del desarrollo.
- **Ensayos conservados:** YOLO11-1 y YOLO26-1, entrenados sobre la misma copia de datos y partición.

La validación actual contiene niveles suficientes y no evaluables, pero carece de ejemplos vacíos y de baja disponibilidad. **Todavía no permite medir el desempeño del modelo en la detección de faltantes.** La siguiente etapa es ampliar la validación con escenas reales y casos críticos.

Las demostraciones sobre fotografías permiten comprobar el funcionamiento del prototipo; la precisión y generalización requieren evaluación con anotaciones y datos independientes.

## 📁 Organización del proyecto

El laboratorio utiliza la siguiente estructura de trabajo. El dataset completo, los entornos locales y los archivos privados se mantienen separados de la publicación del código.

| Carpeta | Propósito |
| :--- | :--- |
| `Contexto/` | Enunciados y referencias del proyecto. |
| `Documentacion/` | Criterios, guías y procedimientos. |
| `Datos/` | Imágenes, particiones y copias revisadas de anotaciones. |
| `Anotaciones/` | Organización del trabajo de anotación en CVAT. |
| `Modelos/` | Referencias y pesos generales para iniciar entrenamientos. |
| `Experimentos/` | Entrenamientos, métricas, diagnósticos y resultados. |
| `Herramientas/` | Código del panel, preparación de datos y demo de inferencia. |
| `Infraestructura/` | Configuración reproducible de Docker. |
| `Entregables/` | Material preparado para compartir y demostrar el prototipo. |

## ▶️ Demostración

Se dispone de **Walmart Lite**, una aplicación de inferencia con los dos modelos entrenados. Su paquete se distribuye por separado del código fuente.

Con el paquete completo, en Windows x64:

1. Extraer el archivo ZIP.
2. Ejecutar `iniciar.cmd`.
3. Esperar la preparación del entorno, elegir un modelo y subir una fotografía.

El primer inicio requiere Internet y prepara un Python privado con sus dependencias. La demo puede ejecutar inferencia en CPU. También se preparó un cuaderno para Google Colab, cuya ejecución en una sesión real de Colab sigue pendiente de verificación.

La ejecución del laboratorio de entrenamiento requiere además los pesos, el dataset y una instancia de CVAT configurada. El README por sí solo documenta el proyecto; para ejecutar la solución se necesitan sus archivos y recursos correspondientes.

## 📄 Licencias

Los componentes de terceros conservan sus licencias. Ultralytics YOLO se ofrece bajo **AGPL-3.0** o una licencia comercial alternativa; sus condiciones deben considerarse al distribuir el código y los modelos o al integrarlos en otra solución.

- [Licenciamiento de Ultralytics](https://www.ultralytics.com/license).
- [Licencia de CVAT v2.77.0](https://github.com/cvat-ai/cvat/blob/v2.77.0/LICENSE).
