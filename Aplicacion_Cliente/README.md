# Walmart Visión · aplicación cliente

La app cliente muestra las alertas de disponibilidad visual por repisa. El historial se guarda en el navegador y se sincroniza con SQLite en el servidor. Desde la app se exportan CSV, Excel y PDF.

La segmentación de niveles y la estimación de disponibilidad visual se comparten con la [app del equipo](../Aplicacion/README.md). El flujo de marcado manual y los lotes ZIP se encuentran en la app del equipo. [Modelo oficial y métricas](../Documentacion/Modelo_V3_actual.md).

## De la foto a la alerta

1. **Comprobar la foto.** El filtro de calidad marca como `no_evaluable` una captura demasiado borrosa, oscura o sobreexpuesta. [`calidad_foto.py`](../Aplicacion/calidad_foto.py)
2. **Delimitar cada nivel.** El modelo de segmentación devuelve una máscara por nivel, que indica qué píxeles de la foto pertenecen a esa repisa. [`inferencia.py`](../Aplicacion/inferencia.py)
3. **Comprobar obstrucciones.** Un YOLO auxiliar usa `yolo26n-seg.pt` para segmentar personas (`person`, clase COCO `0`). Si la obstrucción alcanza el 15 % del área o del ancho de un nivel, la foto completa pasa a `no_evaluable`. Cuando faltan máscaras válidas de nivel, el límite es el 10 % de la imagen. Entre el 5 % y menos del 15 % de un nivel, se excluyen las columnas tapadas del cálculo. Los carros y otros obstáculos sin máscara de persona quedan sujetos a verificación visual. [`oclusiones.py`](../Aplicacion/oclusiones.py)
4. **Medir la disponibilidad visual.** El estimador busca señales de producto dentro de cada máscara, excluye estructuras como rieles y mide los huecos a lo ancho de la repisa. Esto produce un **índice visual de 0 a 100**. El índice describe la disponibilidad visible en la foto. [`ocupacion_paulo.py`](../Aplicacion/ocupacion_paulo.py) · [`ocupacion_linea_a.py`](../Aplicacion/ocupacion_linea_a.py)
5. **Comprobar el encuadre.** Si la foto corta un nivel por el borde, se marca para revisión. Una lectura `Suficiente` también pasa a `Revisar` si el nivel superior abierto parece truncado. [`vision_v3.py`](../Aplicacion/vision_v3.py) · [`geometria_niveles.py`](../Aplicacion/geometria_niveles.py)

| Resultado por nivel | Cuándo aparece |
|---|---|
| **Revisar** | El encuadre, una obstrucción o una señal visual ambigua impiden decidir con confianza. Por ejemplo, un frente continuo con envases oscuros puede producir un índice bajo y requerir revisión. |
| **Reponer** | Hay evidencia suficiente y el índice queda bajo **52**, o se detecta un hueco importante en el frente aunque el índice esté por encima del umbral. |
| **Suficiente** | El índice es de **52 o más** y las reglas de huecos y visibilidad permiten aceptar la lectura. |

La interfaz y el CSV muestran la severidad (`Crítica`, `Alta`, `Normal`, `Verificar`) y conservan el índice bruto (`raw_pct`) cuando hay un valor disponible para el nivel en revisión. La app vuelve a analizar las fotos cuando cambia la revisión del motor en el servidor. [Casos límite documentados](../Documentacion/Modelo_V3_actual.md)

## Descargar e iniciar

[Descarga el MVP](../Entregables/README.md), extrae el ZIP completo y abre **iniciar_cliente.cmd** en la raíz. En un clon, usa el [iniciador de esta carpeta](iniciar_cliente.cmd). El primer inicio requiere Internet para preparar Python 3.12 y sus dependencias. Abre **http://127.0.0.1:8098** o la dirección que indique la consola si el puerto está ocupado.

En macOS o Linux, consulta la [instalación manual](../README.md#instalación-manual-y-configuración). La configuración Docker conjunta monta esta carpeta en solo lectura y SQLite necesita escritura al iniciar. [Límites de ejecución en Docker](../Documentacion/Verificacion_funcional.md#5-empaquetado-y-límites-de-plataforma).

## Usar la app

1. Pulsa **Probar un pasillo de ejemplo** para abrir los [ocho casos precargados](ejemplos/README.md), o carga fotos JPG, PNG o WebP de hasta 10 MB y 24 megapíxeles por foto.
2. Revisa las vistas **Con niveles**, **Foto original** y **Huecos**. En escritorio también puedes usar **Comparar**. Las flechas **← / →** recorren las fotos del filtro activo. En móvil, usa **Góndolas**, **Foto** y **Plan**.
3. Filtra por **Con alertas**, **Requieren revisión** o **Sin alertas**. Si una foto trae alertas y niveles dudosos, aparece en **Con alertas**, y el detalle de cada nivel conserva su estado.
4. En **Más opciones**, descarga el CSV del recorrido o del filtro. Excel y PDF se generan a partir del historial analizado en el servidor.

El primer análisis puede tardar más mientras se prepara el modelo. **Limpiar pasillo** borra el recorrido de este navegador y solicita limpiar el historial compartido. Los archivos originales en tu equipo se conservan. [Manual de las apps](../Documentacion/Usar_Walmart_Vision.md).

## Comprobar o desarrollar

```powershell
.\iniciar_cliente.cmd --verificar
```

Desde la raíz con el entorno de desarrollo preparado:

```powershell
.\.venv-modelo\Scripts\python.exe .\Aplicacion_Cliente\app_cliente.py --check
.\.venv-modelo\Scripts\python.exe -m unittest discover -s Aplicacion_Cliente\Pruebas -v
```

La [guía del equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md) explica el marcado y
la devolución de lotes.

Prueba opcional de memoria y persistencia, con Node.js, Playwright y Edge instalados:
`node Aplicacion_Cliente/Pruebas/test_sesion_cliente.cjs` desde la raíz. Genera imágenes
de ruido y usa un perfil aislado, sin inferencia ni acceso al recorrido del usuario.
`WALMART_PLAYWRIGHT` permite indicar el módulo Playwright y `WALMART_CHROMIUM`, otro
ejecutable Chromium. Los resultados y capturas quedan en `.tmp/cliente_memoria_20261111/`.

## Licencia

Código original del equipo: [AGPL-3.0-only](../LICENSE). Consulta [licencias y procedencia de datos/pesos](../LICENCIAS.md) y [avisos de terceros](../NOTICE.md). Los datos no reciben una licencia pública por este acuerdo sobre el código.
