# Recursos de ejemplo

El uso de las seis imágenes reales y sintéticas se explica en [Usar Walmart Visión](../Historico/Uso_Walmart_Vision_V2.md#probar-con-imágenes-de-ejemplo), junto con la descarga desde Drive y los estados de referencia.

- `imagenes_demo_20261020.json` conserva la selección, las fuentes y los hashes del ZIP.
- `LEEME_imagenes_demo_20261020.txt` es el texto versionado incluido en ese paquete; permite regenerarlo sin cambiar sus bytes publicados.
- `nivel_ocluido_carro_050.png` y su prompt son una ilustración didáctica de la anotación bajo oclusión. No son una anotación completa ni validada del lote.

## Ilustración de un nivel parcialmente oculto

La ilustración se generó a partir de una edición sintética de la foto 050. El contorno muestra el penúltimo nivel completo, incluida su parte oculta, para explicar la propiedad `Occluded`; no asigna un estado definitivo de disponibilidad. También debe revisarse el último nivel: si no se puede establecer su geometría, se registra una incidencia en lugar de inventar el contorno.

La [guía de anotación](../Desarrollo/Guia_anotacion.md#oclusiones-y-geometría) contiene las reglas sobre geometría, evidencia visible y estados.
