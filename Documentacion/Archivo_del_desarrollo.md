# Archivo del desarrollo y alcance del repositorio

El árbol actual reúne las apps cliente y equipo, su motor, el único modelo oficial, pruebas, construcción de paquetes y documentación. Las carpetas académicas [Fase 1](../Fase%201/) y [Fase 2](../Fase%202/) conservan sus rutas y bytes.

## Herramientas internas y antecedentes

CVAT sirvió para anotar y revisar el dataset propio. El laboratorio permitió preparar datos y entrenar con la GPU local sin depender de Colab, además de consultar métricas y curvas. Estas herramientas no son requisitos de ejecución de las apps. Sus fuentes publicadas y los registros anteriores siguen disponibles en una revisión fija:

- [Árbol completo anterior](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd).
- [Laboratorio y entrenamiento GPU](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Laboratorio).
- [Registros y procedencia de datos](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Datos).
- [Configuración de infraestructura](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Infraestructura).
- [Experimentos y documentos históricos](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Historico).
- [Documentación técnica anterior](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo).
- [Evaluadores, etiquetador y visor de ocupación internos](https://github.com/vcanio/Capstone2026/tree/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Laboratorio/Ocupacion).

La retirada del árbol actual no elimina esos commits ni altera tags o releases. Las releases conservan sus propios ZIP; no se afirma que cada ZIP incluya todas las herramientas. Los datasets privados, entornos, recibos completos, pesos opcionales y cambios locales no publicados permanecen en el entorno del equipo: GitHub no es su respaldo completo.

## Qué conserva esta simplificación

El modelo oficial y el código ejecutable de ambas apps conservan sus bytes respecto de la revisión anterior. Línea A sigue con índice visual 0–100, umbral 52 y ajuste preliminar. La candidata basal del 12/11 permanece como ensayo local y no se publica por esta reorganización. No se entrena, se modifica CVAT ni se usa test para la simplificación.

Las guías mantienen datos, criterios de anotación, correcciones asistidas, resultados, límites de evaluación y acceso a los antecedentes. El verificador y el empaquetador actuales están en [Distribucion](../Distribucion/README.md), sin depender del antiguo laboratorio.
