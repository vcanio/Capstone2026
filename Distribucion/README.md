# Comprobar y empaquetar las apps

Estos scripts usan la biblioteca estándar de Python 3.12 y Git. No requieren el laboratorio, CVAT, datos privados ni entrenamiento. El preparador Windows conserva uv y sus licencias dentro de Aplicacion/herramientas.

## Verificación

Desde la raíz de un clon:

```bash
python Distribucion/verificar.py
python -m compileall -q Aplicacion Aplicacion_Cliente Distribucion
```

El verificador comprueba el único peso oficial, los hashes del motor y de uv, los enlaces Markdown locales, la sintaxis Python y los hashes e inventario de Fase 1/Fase 2. Rechaza carpetas internas, pesos adicionales, campos secretos conocidos y binarios no previstos en los archivos publicables. No certifica ausencia de cualquier secreto posible ni evalúa precisión del modelo.

Con las dependencias de Aplicacion/requirements.txt instaladas, en Linux/macOS:

```bash
PYTHONPATH=Aplicacion python -m unittest discover -s Aplicacion/Pruebas -v
PYTHONPATH=Aplicacion:Aplicacion_Cliente python -m unittest discover -s Aplicacion_Cliente/Pruebas -v
python -m unittest discover -s Distribucion/tests -v
```

En PowerShell, establecer `$env:PYTHONPATH='Aplicacion;Aplicacion_Cliente'` antes de ejecutar las mismas órdenes de unittest. Node permite ejecutar las pruebas de interfaz con DOM simulado. La prueba adicional Aplicacion_Cliente/Pruebas/test_sesion_cliente.cjs requiere Playwright y Chromium; no descarga ni usa datos privados.

## Construcción desde un clon limpio

```bash
python Distribucion/empaquetar.py --output /ruta/nueva/Walmart_Vision_Cliente_y_Equipo.zip
```

Crear primero un commit de las fuentes y comprobar `git status --porcelain` vacío. El empaquetador verifica el producto, copia ambas apps, un solo motor/peso, guías, licencias, Compose y los scripts de distribución. No incluye Fase 1/Fase 2, el PDF académico, tests, fotos ni entornos. Conserva sus referencias como enlaces al commit fuente. FUENTE.json identifica la fuente y MANIFIESTO_SHA256.json identifica cada archivo; el ZIP tiene un .sha256 independiente. Se rechaza sobrescribir entregas existentes.

Comprobar el ZIP en una extracción temporal, con HTTP e inferencia CPU de ambas apps:

```bash
python Distribucion/comprobar_paquete.py --zip /ruta/nueva/Walmart_Vision_Cliente_y_Equipo.zip
```

Por defecto usa una imagen blanca generada y comprueba el funcionamiento, sin medir precisión. `--foto` permite usar una foto de desarrollo autorizada, nunca test reservado. Informar por separado la validación Compose, el build Docker y la prueba física en Mac. Estas comprobaciones son funcionales, no evaluación final de precisión.

## Publicación

Hacer commit y push sin forzar; esperar el CI del commit exacto. Publicar una release solo cuando se solicite una entrega nueva, con tag y nombre de ZIP nuevos, licencia y acceso a su código fuente correspondiente. Verificar la descarga pública contra el checksum. No reemplazar activos, tags o ZIP anteriores. La simplificación del árbol no cambia la entrega publicada del 11/11.

[Producto](../README.md) · [Modelo](../Documentacion/Modelo_V3_actual.md) · [Archivo del desarrollo](../Documentacion/Archivo_del_desarrollo.md).
