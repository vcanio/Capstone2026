# Licencias y procedencia

Estado documentado el 10 de noviembre de 2026, tras la confirmación de Vicente
de que el equipo está de acuerdo con publicar su código bajo AGPL-3.0.

## Código del equipo

Copyright (c) 2026 Vicente Canio, Paulo Guerra y Vicente Vilches.

El código original del proyecto se distribuye bajo **GNU Affero General Public
License, versión 3 (AGPL-3.0-only)**. El texto íntegro está en [LICENSE](LICENSE).
Los avisos de terceros y sus condiciones se conservan en [NOTICE.md](NOTICE.md).
Esta declaración no cambia las licencias de dependencias, documentos de terceros,
fotografías, datos, marcas ni material académico ajeno al código.

El propósito del equipo es 100 % académico. Ese propósito describe el proyecto;
no agrega una restricción de «solo uso académico» a AGPL-3.0. La licencia permite
también uso comercial, sujeto a sus condiciones. La autoría permanece reconocida.

Al distribuir el programa o sus modificaciones se deben conservar los avisos,
proporcionar la licencia y facilitar el código fuente correspondiente conforme a
AGPL-3.0. Su sección 13 añade obligaciones al ofrecer versiones modificadas a
usuarios que interactúan por una red. El código y los scripts de construcción de
la entrega se ofrecen en el repositorio, junto con su modelo operativo.

## Fotografías y anotaciones

Vicente confirmó el 10/11/2026 que las fotografías originales fueron tomadas por
el equipo y las anotaciones fueron realizadas por el equipo a mano usando CVAT.
Se documenta esa declaración de autoría; no se declara una licencia abierta del
dataset ni una autorización de terceros que no haya sido aportada.

El corpus también contiene variantes sintéticas derivadas de las capturas del
equipo, identificadas como tales en los registros. No son nuevas fotografías
reales. Los registros de anotación conservan las revisiones y correcciones
asistidas, incluido el cálculo geométrico de superiores; no se modifican como
consecuencia de esta declaración de autoría.

Las fotografías y anotaciones **no reciben una licencia pública por este acuerdo
sobre el código**. El dataset completo no forma parte del ZIP de las apps. Los
ejemplos o figuras que ya se compartieron no conceden por sí mismos permiso para
redistribuir el resto de los datos. Una futura apertura del dataset requiere
definir expresamente sus condiciones y revisar los permisos aplicables.

Estado: **autoría y finalidad académica documentadas; licencia pública del dataset
no concedida**. No se afirma autorización institucional de Walmart/Líder o DUOC
a partir de la autoría de las fotografías.

## Modelo y pesos

Se verificó la siguiente procedencia en los manifiestos locales de los ensayos:

1. Base preentrenada: **YOLO26 nano de segmentación**, `yolo26n-seg.pt`, de
   Ultralytics. SHA-256:
   `361fbfabab285c3237700b6bb91d7ecfa602cd945fffda8dbe1242829b71e73f`.
2. Primer afinado de esta cadena:
   `v3_segmentacion_sin_tapadas_20261102_202529_4bb3`, best.pt SHA-256
   `2ba37c853b88648e03b9a72309cfbc4179ef05f9c67452bb968f3bfb1a96ff70`.
3. Refuerzo del 5/11:
   `v3_refuerzo_geometria_revision_20261105_022414_e6f0`, best.pt SHA-256
   `7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a`.

4. Cierre revisado adoptado el 10/11:
   `v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c`, best.pt SHA-256
   `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`.
   Parte del refuerzo del 5/11.

El peso distribuido se identifica en [Aplicacion/modelos.json](modelos.json).
Se usa Ultralytics 8.4.174. Los pesos son un afinado del modelo preentrenado;
no se presentan como una arquitectura o un entrenamiento desde cero del equipo.

Ultralytics ofrece sus modelos y software bajo AGPL-3.0 o una licencia Enterprise;
su documentación incluye los modelos entrenados y afinados. El proyecto adopta
la vía **AGPL-3.0**, con las aportaciones del equipo bajo esa licencia. No se
declara una licencia Enterprise adquirida. La finalidad académica no exime de
cumplir AGPL-3.0 ni sustituye los permisos de los datos.

Estado: **procedencia verificada y condiciones AGPL-3.0 identificadas y adoptadas**.
Esto no constituye una certificación de derechos sobre datos o materiales de
terceros ni una evaluación de precisión del modelo.

## Fuentes de las condiciones

- [GNU AGPL-3.0, texto oficial](https://www.gnu.org/licenses/agpl-3.0.en.html).
- [Cómo aplicar las licencias GNU](https://www.gnu.org/licenses/gpl-howto.en.html).
- [Licenciamiento de Ultralytics](https://www.ultralytics.com/license).
- [Documentación oficial de YOLO26](https://docs.ultralytics.com/models/yolo26/).

Esta actualización no modifica pesos, particiones, anotaciones, inferencia ni
activos de releases anteriores. Las entregas posteriores incluyen estos avisos.
