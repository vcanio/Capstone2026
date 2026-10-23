# Entregables

## Aplicación local actual

[**Walmart_Vision_Actual_20261023.zip**](Walmart_Vision_Actual_20261023.zip) · [SHA-256](Walmart_Vision_Actual_20261023.sha256).

Incluye el visor, iniciador Windows, archivos Docker para Mac y **dos modelos V2: YOLO11 y YOLO26**. La revisión del 23/10 alinea las instrucciones y metadatos; conserva los pesos, la inferencia y la interfaz de la entrega anterior. No incorpora un modelo V3 ni un entrenamiento nuevo.

Para usar: extraer todo el ZIP y abrir `Walmart_Vision/iniciar.cmd` en Windows. En Mac, abrir Docker Desktop y ejecutar `docker compose up --build -d --wait` dentro de `Walmart_Vision`. [Manual completo](../Documentacion/Usar_Walmart_Vision.md).

El paquete es una preparación local. Este ordenamiento no publica ni reemplaza activos en GitHub. Los paquetes publicados anteriormente se identifican por sus fechas y manifiestos históricos.

[Cuaderno para Colab](Probar_en_Colab.ipynb): también está dentro del ZIP. La ejecución remota de Colab no se certifica mediante las comprobaciones locales.

## Antecedente conservado

[Walmart_Vision_Actual_20261022.zip](Walmart_Vision_Actual_20261022.zip) y [su hash original](Walmart_Vision_Actual_20261022.sha256) mantienen sus bytes. La documentación antigua incluida en ese ZIP corresponde a su preparación original. No confundirlo con otras distribuciones históricas que incluían cuatro modelos V1/V2.

## Informe intermedio

- [PDF](Informe_Intermedio_Avance_20261020.pdf), [Word](Informe_Intermedio_Avance_20261020.docx) y [HTML](Informe_Intermedio_Avance_20261020.html): copias del informe fechado y sus revisiones documentadas. Se conservan como entrega académica, sin reescribir sus resultados durante esta limpieza.
- [Fuente Markdown](../Documentacion/Informe_Intermedio_Avance_20261020.md) y [evidencias](../Documentacion/Evidencias/README.md).

Los paquetes de datos y modelos del laboratorio se distribuyen por separado y no son necesarios para usar el visor. [Reproducir el laboratorio](../Documentacion/Desarrollo/Replicar_proyecto.md).
