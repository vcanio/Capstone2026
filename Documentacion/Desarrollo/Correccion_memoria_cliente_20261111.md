# Corrección de memoria del cliente · 11 de noviembre de 2026

> Nota de vigencia: el cliente recibió después el flujo de alertas y revisión humana y la limpieza definitiva. Véase [estado actual del cliente](Cliente_alertas_20261111.md). Las comprobaciones siguientes corresponden a la intervención fechada que describen.

Vicente entregó una captura de Brave en `127.0.0.1:8098` con «Aw, Snap!» y
«Error code: Out of Memory». Es un cierre de la pestaña por falta de memoria,
no un indicador normal de preparación del primer análisis. La captura no contiene
un perfil de memoria que permita atribuir por sí solo todas las asignaciones del fallo.

La primera revisión había medido el servidor Python en torno a 1,1 GB con poca CPU.
Eso no medía el pico del renderizador del navegador. En la lectura posterior al cierre,
Windows tenía unos 7,5 GB de RAM disponibles y C: unos 84 GB libres. El espacio escaso
observado anteriormente ya no era su estado actual; no se atribuye este cierre solo al disco.

## Cambios locales

- Las miniaturas ya no referencian cada original de alta resolución. Se generan bajo
  demanda con un lado máximo de 160 px, decodificando un original a la vez y liberando
  el bitmap y el lienzo temporal. Solo las miniaturas próximas al área visible se preparan.
- La navegación escribe un manifiesto con IDs y selección. Fotos modificadas se guardan
  individualmente en IndexedDB. Los cambios se agrupan y hay una sola escritura en curso,
  sin la cola anterior de instantáneas completas creadas con `structuredClone`.
- Las vistas anotadas conservan sus bytes como Blob; sus URL temporales no se persisten.
  Se liberan URL de fotos retiradas y fuentes de imágenes en visores ocultos.
- La base local pasa a versión 2. La migración de la sesión anterior, incluidos archivos,
  diagnósticos, contornos, verificaciones, reposiciones y limpieza reversible, sustituye
  el registro anterior en la misma transacción que confirma el nuevo formato. Un fallo
  conserva la sesión anterior; una recuperación incompleta no sobrescribe el recorrido.
- El inicio indica «Recuperando el recorrido guardado…». Se conserva el aviso específico
  del primer análisis. Limpiar durante una petición en curso no inicia nuevas inferencias
  para las fotos que acaban de pasar a la reserva de deshacer.

Solo cambian el cliente, su documentación y pruebas. Se conservan el motor compartido,
la ocupación y los pesos oficiales. No se ejecutó inferencia sobre fotografías reales,
no se modificaron CVAT, particiones o datasets y no se publicó una nueva entrega.

## Evidencia y límites

Prueba aislada en Edge/Chromium con JPEG de ruido de 2048 × 1536 y resultados simulados.
La comparación antes/después se limitó a ocho fotos para evitar otra presión innecesaria
sobre el equipo. Doce selecciones en el mismo turno de JavaScript:

| Medida | Antes | Después |
| --- | ---: | ---: |
| Instantáneas completas mediante `structuredClone` | 12 | 0 |
| Fotos incluidas en las escrituras completas | 96 | 0 |
| Escrituras de estado | 12 | 1 |
| Píxeles fuente sumados de las ocho miniaturas | 25.165.824 | 153.600 |
| Lado máximo de miniatura | 2048 px | 160 px |

Los píxeles fuente y las copias son medidas del trabajo evitado, no una medición de
la RAM máxima del navegador ni una garantía de que ningún lote pueda agotar memoria.
Los clics de una persona en turnos separados pueden producir más de una escritura,
pero siguen sin incluir las imágenes del recorrido completo.

Ensayo adicional: 68 fotos simuladas (66 activas y dos en deshacer). Cien selecciones
en el mismo turno produjeron una escritura de estado y cero escrituras de fotos.
Pasaron la migración, comprobación SHA-256 de un original de muestra, conservación
de contornos y marcas, recarga, limpieza y deshacer persistentes, guardado abortado y
reintento, y migración abortada conservando v1 hasta el reintento. Verificados escritorio
y móvil de 390 px sin desbordamiento de página. Las nueve pruebas HTTP/unitarias del
cliente pasaron con motor simulado; el aviso del primer análisis también pasó su prueba
de navegador. Detector de UI sin hallazgos.

Prueba reproducible: `Aplicacion_Cliente/Pruebas/test_sesion_cliente.cjs`.
Recibos locales: `.tmp/cliente_memoria_20261111/resultado.json`, `escritorio.png`,
`movil.png` y respaldo `interfaz_antes.html`. Ninguna prueba accedió al perfil Brave
de Vicente ni a sus registros IndexedDB reales. La recuperación de su recorrido se
ejecutará al recargar el cliente actualizado en el mismo navegador y dirección.
