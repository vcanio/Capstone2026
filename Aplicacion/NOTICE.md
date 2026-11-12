# Autoría y avisos de terceros

Walmart Visión · Capstone DUOC UC · 2026.

Copyright (c) 2026 Vicente Canio, Paulo Guerra y Vicente Vilches, respecto del
código original del equipo. GNU AGPL-3.0-only; véase LICENSE y LICENCIAS.md.
Se distribuye sin las garantías excluidas por la licencia.

La denominación del proyecto y las referencias a Walmart/Líder no atribuyen
autoría, patrocinio ni aprobación institucional a esas entidades.

## Código fuente de la entrega

Repositorio: https://github.com/vcanio/Capstone2026

Fuente correspondiente a la entrega con avisos de licencia:
https://github.com/vcanio/Capstone2026/tree/walmart-vision-apps-prueba-2026-11-11

Archivo de fuentes de ese tag:
https://github.com/vcanio/Capstone2026/archive/refs/tags/walmart-vision-apps-prueba-2026-11-11.zip

La raíz del repositorio contiene los scripts de empaquetado, las dependencias
fijadas y las instrucciones de ejecución. El código original de los componentes
portátiles se conserva en Aplicacion y Aplicacion_Cliente. El peso operativo está
en Aplicacion/modelos y se identifica por SHA-256 en Aplicacion/modelos.json.

## Dependencias principales

Los componentes de terceros conservan sus derechos, avisos y licencias.
La siguiente tabla identifica sus condiciones principales; los paquetes
instalados pueden incluir avisos adicionales de sus propios componentes.

| Componente | Condición principal | Fuente |
|---|---|---|
| Ultralytics 8.4.174 y YOLO26 | AGPL-3.0 en la vía adoptada por este proyecto | https://github.com/ultralytics/ultralytics/blob/v8.4.174/LICENSE |
| PyTorch 2.5.1 | BSD-3-Clause | https://github.com/pytorch/pytorch/blob/v2.5.1/LICENSE |
| Torchvision 0.20.1 | BSD-3-Clause | https://github.com/pytorch/vision/blob/v0.20.1/LICENSE |
| NumPy 1.26.4 | BSD-3-Clause; avisos adicionales en sus distribuciones binarias | https://github.com/numpy/numpy/blob/v1.26.4/LICENSE.txt |
| Pillow 12.3.0 | MIT-CMU | https://github.com/python-pillow/Pillow/blob/12.3.0/LICENSE |
| OpenCV / opencv-python 4.11.0.86 | Apache-2.0; avisos adicionales de las bibliotecas incluidas en cada paquete | https://github.com/opencv/opencv/blob/4.11.0/LICENSE |
| Shapely 2.1.2, usado en laboratorio y comprobaciones | BSD-3-Clause; componentes como GEOS conservan sus condiciones | https://github.com/shapely/shapely/blob/2.1.2/LICENSE.txt |
| uv, ejecutable incluido para preparar Windows | Apache-2.0 OR MIT | herramientas/fuente_uv.json y herramientas/licencias/ |

Las dependencias Python se descargan durante la preparación; no se incluyen
sus wheels ni un entorno instalado en el ZIP. El ejecutable uv distribuido sí
incluye sus textos Apache y MIT. CVAT fue la herramienta de anotación: su uso no
convierte las anotaciones del equipo en código de CVAT ni les asigna su licencia.

Las fotografías, anotaciones, figuras y documentos ajenos al código no quedan
relicenciados por este aviso. Sus condiciones se explican en LICENCIAS.md.
