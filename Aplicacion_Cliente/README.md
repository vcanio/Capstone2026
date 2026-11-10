# Walmart Visión · aplicación cliente

Interfaz de prueba para supervisores y equipos de reposición: priorización de fotos,
diagnóstico por nivel, checklist «Repuesto» y hoja de reposición CSV para Excel.
Comparte el modelo V3 oficial y el motor de [Aplicacion](../Aplicacion/README.md).

Línea A usa un **índice visual preliminar de 0 a 100, con umbral 52**. No es porcentaje
físico de stock ni detector de personas u obstáculos. Revisa los contornos y la foto.
Esta entrega no constituye una evaluación final del flujo operativo.

| Aplicación | Uso | Dirección local |
|---|---|---|
| Cliente | Prioridades, checklist y CSV | http://127.0.0.1:8098 |
| Equipo | Controles técnicos, comparación, marcado y lotes de revisión | http://127.0.0.1:8095 |

## Descargar e iniciar

La [versión de prueba del 10/11](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10)
incluye ambas apps y el modelo. Extrae todo el ZIP.

En Windows x64, abre `iniciar_cliente.cmd` en la raíz del paquete o
[iniciar_cliente.cmd](iniciar_cliente.cmd) desde esta carpeta. El primer inicio prepara
Python 3.12 y dependencias dentro de Aplicacion; necesita Internet. No requiere instalar
el laboratorio. Si existe el entorno de desarrollo `.venv-modelo`, lo reutiliza.

Desde un clon, el mismo iniciador funciona con el peso incluido en `Aplicacion/modelos`.
El preparador Windows también está incluido en Git.

Para macOS/Linux con Docker Desktop, desde la raíz del proyecto o paquete:

```bash
docker compose -f compose.apps.yaml up --build -d --wait
```

Abre las direcciones de la tabla. Para detener ambas apps:
`docker compose -f compose.apps.yaml down`.

Cada persona ejecuta una copia local. No hay sincronización entre computadores.
Carga fotos propias: el dataset y las fotos del catálogo de demostración local no se
distribuyen en este ZIP. La app del equipo exporta lotes de revisión para compartir;
la app cliente descarga la hoja CSV.

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
la devolución de lotes. La release del 5/11 conserva su versión anterior.
