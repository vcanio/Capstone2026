# Publicar fuentes y mantener la release V3

Walmart Vision V3 está publicada en la [release del 26 de octubre de 2026](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-10-26), con el ZIP y su SHA-256. Una reorganización de fuentes actualiza main y sus enlaces; no crea otra release ni modifica los activos existentes.

## Preparar una actualización

1. Trabajar sobre una copia aislada del main remoto actual y conservar los cambios concurrentes. El checkout local de distribución puede contener trabajo previo y no debe sincronizarse automáticamente.
2. Organizar fuentes en Aplicacion y Laboratorio, registros anteriores en Historico y material académico en sus carpetas originales Fase 1 y Fase 2. Los manifiestos y snapshots fechados conservan sus bytes; los lectores traducen prefijos anteriores.
3. Revisar el diff completo. Mantener fuera de Git fotos, pesos, ZIP, entornos, .env, contexto privado y respaldos. Preservar todos los archivos académicos ya publicados.
4. Ejecutar las pruebas de Aplicacion, Laboratorio/Datos y Laboratorio/Reproducibilidad/tests, más la auditoría `python Laboratorio/Reproducibilidad/verificar_publicacion.py` en el checkout preparado. La auditoría distingue archivos presentes de activos declarados distribuibles.
5. Publicar un commit sobre el HEAD revisado, sin forzar la rama, y comprobar GitHub Actions, enlaces y hashes de los activos.

## Distribución vigente

El [ZIP V3 publicado](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-10-26/Walmart_Vision_V3_20261027.zip) incluye el modelo y funciona con el iniciador Windows o el procedimiento Docker del [manual](../Usar_Walmart_Vision.md). Los archivos automáticos Source code contienen fuentes sin pesos.

Los empaquetadores conservan funciones históricas con nombres y manifiestos fechados. No deben usarse sus valores antiguos para reemplazar la release vigente. Una entrega futura necesita un paquete y tag nuevos, comprobaciones explícitas y autorización para publicarla.

Las imágenes de demostración mantienen su [carpeta de Drive](https://drive.google.com/drive/folders/1z0-GNiRUJcVwbjLVkiDc20G2F8f9QASS?usp=sharing). La reorganización no modifica ese contenido ni lo convierte en una evaluación V3.

[Distribución actual](../../Entregables/README.md) · [Reorganización pública](Reorganizacion_GitHub_20261026.md) · [Mapa](Mapa_del_proyecto.md).
