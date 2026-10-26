> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../Modelos/Actual/README.md).

# Auditoría de main · 22 de octubre de 2026

Resultado: **main contiene exactamente los archivos de la última release publicada y supera las comprobaciones ejecutadas, pero aún hay referencias operativas desactualizadas y no hay protección de la rama**. Esto valida el estado comprobado; no garantiza que futuras incorporaciones sean estables ni certifica la precisión de ocupación visual.

## Estado remoto comprobado

- Repositorio: [vcanio/Capstone2026](https://github.com/vcanio/Capstone2026). Rama predeterminada: `main`.
- Commit de main: `2c68440cc32061aeb1d8078f6864f65fb0694001`.
- Release más reciente consultada: [Walmart Visión · Windows y macOS](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-2026-10-22), publicada, sin marcas de borrador o prerelease.
- Commit de la release: `0cb7cc09e772c3db893e260ec59503a67a9d29c5`. Main tiene un commit adicional, el merge del PR 3, sin diferencias de archivos respecto de la release.
- Árbol Git compartido por ambos commits: `8575dd2d399544d74243839fea3ce030bbb900e7`.
- [GitHub Actions del commit actual](https://github.com/vcanio/Capstone2026/actions/runs/39728074664): completado correctamente.
- No había PR abiertos en la consulta. La rama `Paulo` no tiene commits exclusivos respecto de main y está 29 commits detrás. La rama de la release apunta a su commit publicado; su permanencia no significa que falte integrar código.
- Main figura con `protected=false` y la consulta de rulesets del repositorio devuelve una lista vacía. Los checks existen, pero no hay una regla de protección que obligue a aprobarlos antes de incorporar cambios.

## Comprobaciones sobre los archivos publicados

Se utilizó la copia limpia en `.publicacion/vision_ocupacion_20261022/source`, situada en el commit de la release. Su árbol Git coincide con el de main remoto; su estado era limpio antes y después de las comprobaciones.

| Comprobación | Resultado |
|---|---|
| Auditoría `verificar_publicacion.py` | Correcta: 925 archivos Git y 5 paquetes declarados. |
| Sintaxis Python | 87 archivos correctos. |
| Enlaces Markdown | 482 destinos disponibles y 16 destinos declarados en activos descargables. |
| Restricciones de publicación del verificador | Sin rutas privadas, pesos/ZIP, archivos de 50 MiB o más ni campos JSON de credenciales rechazados por sus reglas. No es una auditoría exhaustiva de secretos o del historial Git. |
| Suite de Historico/Reproducibilidad | 15 pruebas, todas correctas. |
| Suite de la aplicación y transiciones de interfaz | 27 pruebas, todas correctas, sin omisiones informadas. |
| Integridad del ZIP local vigente | SHA-256 coincide con el digest del activo publicado en GitHub. |

ZIP: `Walmart_Vision_Ocupacion_20261022.zip`.

SHA-256: `4419accccdbf36073cb32785a3c18ff43543228f234a90b7b0814d35fb74917e`.

Las pruebas se ejecutaron con Python 3.12.14. El primer intento local encontró restricciones del entorno de ejecución en temporales y HTTP local; la repetición con temporales dentro del proyecto y permisos de ejecución adecuados terminó correctamente. Logs de la ejecución correcta: `.tmp/auditoria_main_20261022/publicacion.log`, `reproducibilidad.log` y `demo.log`. No se repitió inferencia con los cuatro modelos ni se probó un Mac físico durante esta auditoría.

## Hallazgos que impiden dar todo por actualizado

1. **Preparador general con la entrega anterior.** `Laboratorio/Reproducibilidad/empaquetar_publicacion.py`, líneas 73 y 108, conserva el tag por defecto y el ZIP del 20 de octubre. Su ejecución completa reconstruye el manifiesto con esa selección. Cambiar solo `--tag` no cambia el nombre del ZIP. La guía `Documentacion/Desarrollo/Publicar_GitHub.md`, línea 24, ya reconoce esta limitación y explica el flujo explícito usado para la entrega nueva. La release vigente es correcta; queda deuda en la herramienta general.
2. **Guías con referencias vigentes contradictorias.** `Historico/Reproducibilidad/VERIFICACION.md`, líneas 4–7, y `Documentacion/Desarrollo/Trabajo_en_equipo.md`, líneas 367–370, todavía presentan la entrega del 20 de octubre como actual. Deben apuntar a la entrega del 22 de octubre o identificar esos párrafos como históricos. El README principal, la guía de usuario, el índice de entregables y la guía de publicación sí apuntan a la entrega nueva.
3. **Estado de datos desactualizado.** `Datos/Registros/README.md`, línea 17, indica que la importación y el entrenamiento de la tarea 19 siguen sin habilitar. Esto contradice el README principal y `Laboratorio/Experimentos/README.md`, que identifican los dos ensayos V2 ya ejecutados sobre esa tarea. La frase debe quedar como antecedente o actualizarse al estado registrado.
4. **Protección de main pendiente.** Para sostener el criterio de estabilidad en futuras incorporaciones, configurar revisión mediante PR y checks obligatorios. Esta auditoría no cambió la configuración del repositorio.

## Material antiguo que conserva una función

- `Historico/Documentacion/` tiene un índice que explica su condición histórica y enlaza la documentación vigente.
- `Datos/Registros/Versiones_modelos/`, las particiones, los snapshots y las métricas conservan las entradas y resultados de los ensayos reproducibles. El índice de registros pide conservar sus bytes.
- Las fuentes congeladas de experimentos permiten comprobar cómo se obtuvieron los resultados. Además, `Laboratorio/Modelos/ocupacion_paulo.py`, línea 76, todavía lee `Laboratorio/Experimentos/Bordes/Versiones/gondola_bordes_paulo_20261020.py` para registrar su procedencia. Borrar esa carpeta por su fecha puede romper funciones vigentes.
- El material académico de `Fase 1/` se conserva expresamente según la guía de publicación y las pruebas del publicador.
- Los ZIP de versiones anteriores están en Releases; no aparecen como archivos ZIP versionados en el árbol revisado.

No se identificaron archivos temporales publicables que pudieran eliminarse con certeza solo por su antigüedad. La revisión de nombres, reglas de publicación, índices y dependencias no demuestra que no exista ningún archivo sin uso; no se hizo una prueba exhaustiva de alcanzabilidad de todo el repositorio.

## Diferencia con el laboratorio local

La carpeta raíz `C:/Proyectos/Walmart` funciona como laboratorio y no tiene `.git`. La copia `.publicacion/repositorio` conserva main en `6123db1`, metadatos remotos antiguos, archivos modificados y material nuevo sin seguimiento. No debe confundirse ese estado con el main actual consultado directamente en GitHub ni actualizarse mediante reset o descarte de cambios.

Los criterios V3 y las revisiones CVAT más recientes están en el laboratorio y todavía no forman parte del árbol estable publicado. Su ausencia no significa que se haya perdido la release: requieren una integración separada y revisada. Se conservan los respaldos y registros de los jobs 67, 68 y 69; no se modificaron anotaciones ni se duplicaron superiores.

Esta intervención produjo únicamente este informe local. No se hicieron commits, push, eliminaciones de archivos del proyecto ni cambios en ramas o Releases de GitHub.
