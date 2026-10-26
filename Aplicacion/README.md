# Walmart Vision · Aplicación V3

Fuentes del visor vigente. Para usar la aplicación con su modelo, descarga el [ZIP V3 publicado](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-10-26), extráelo completo y sigue el [manual](../Documentacion/Usar_Walmart_Vision.md).

- Windows: abrir `Walmart_Vision/iniciar.cmd` en la descarga.
- macOS y Docker: ejecutar `docker compose up --build -d --wait` dentro de `Walmart_Vision` y abrir http://127.0.0.1:8095.
- [Modelo y límites](../Modelos/Actual/README.md) · [Guía V3](LEEME_V3.md) · [Distribución](../Entregables/README.md).

La app identifica niveles con confianza 0,60. La ocupación es experimental y la visibilidad se confirma manualmente. Las fotos se procesan en memoria. El archivo automático Source code no incluye pesos ni reemplaza la descarga de la release.
