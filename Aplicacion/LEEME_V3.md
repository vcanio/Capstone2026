# Walmart Vision · V3

Interfaz local simplificada del 26 de octubre de 2026, sobre el modelo cerrado e integrado por decisión de Vicente el 25. Incluye únicamente el `best.pt` del afinado de papeles, huevos y superiores vacíos. El historial de los modelos anteriores se conserva en la documentación del proyecto.

## Usar la aplicación

En Windows, extraer todo el ZIP y abrir `iniciar.cmd`. En Docker, ejecutar `docker compose up --build -d --wait` desde la carpeta extraída. Abrir http://127.0.0.1:8095. La primera preparación puede requerir conexión para instalar dependencias; después la inferencia es local. Las fotos no se guardan ni se incorporan al entrenamiento.

1. Seleccionar una foto JPG, PNG o WebP de hasta 15 MB.
2. Indicar cómo se ve la góndola: completa y despejada, recortada, con un objeto delante o con una persona tapándola. Esta comprobación es manual: el modelo no detecta automáticamente la visibilidad.
3. El análisis usa automáticamente el modelo vigente, detección de niveles y bordes, con confianza fija 0,60. No requiere configuración técnica.
4. Pulsar Analizar foto. Revisar contornos, ocupación estimada, alcance y avisos. Original, Niveles, Bordes y Comparar permiten comprobar el resultado.

## Fotografías frontales

**Para usar esta versión, toma fotos frontales o casi frontales de la góndola.** Sitúate frente al tramo, mantén la cámara nivelada y procura que se vean sus dos extremos y las superficies de apoyo. Evita tomas desde un costado, desde muy arriba o abajo, panorámicas deformadas, desenfoque y reflejos fuertes. Si el mueble es largo, utiliza varias tomas frontales de tramos completos.

La perspectiva oblicua cambia las alturas y anchuras aparentes, oculta huecos detrás de los productos y puede desplazar las máscaras. El algoritmo estima una proporción de la imagen, sin reconstruir el volumen ni corregir automáticamente la perspectiva. Una foto frontal ayuda, pero no garantiza una detección correcta: revisa siempre los contornos y la visibilidad. No hay un ángulo máximo validado ni un detector automático que certifique que la toma sea frontal.

## Criterio de nivel y mediana

Un nivel es el área útil completa donde pueden existir productos y huecos, apoyada sobre la repisa, por encima del portaprecio. Se respetan los límites interiores y la cubierta física cuando existe; no se ajusta a los envases ni solo a la franja frontal. Un nivel vacío sigue siendo un nivel.

Si el superior no tiene un techo claro, las anotaciones usan la mediana de las alturas inferiores del mismo tramo, medida en el centro y proyectada desde el apoyo sobre el portaprecio. Por ejemplo, 190, 195, 210 y 220 píxeles producen 202,5 píxeles. Es una convención para mantener el mismo criterio en originales y variantes llenas o vacías. Si la proyección sale de la foto, se recorta y marca parcial. La app conserva las máscaras de YOLO: no recalcula ni fuerza esa mediana durante la predicción.

## Interpretar el resultado

YOLO V3 predice una sola clase: Nivel. Conserva las máscaras del modelo; no impone una mediana ni inventa niveles omitidos. La confianza no es ocupación.

Los bordes son cambios de intensidad de la foto, distintos del contorno del nivel. Se combinan con gradiente, color y textura por celdas dentro de la máscara. El mapa amarillo es esa señal combinada, no producto confirmado. La estimación final combina 70 % de superficie con señal y 30 % de cobertura horizontal: `O = 0,70 × A + 0,30 × W`. Con A = 40 % y W = 80 %, O = 52 %. El ancho exige señal en al menos el 20 % de las celdas utilizables de una columna. Menos del 30 % produce Reponer; desde el 30 %, Suficiente, solo para el área detectada con visibilidad confirmada. Es una estimación experimental pendiente de calibración V3, no una medición exacta de stock.

Cuando la señal se concentra arriba, o queda en la periferia sin suficiente respaldo central e inferior, se muestra Revisar · señal ambigua, sin porcentaje ni decisión de reposición. Puede proceder de cartelería, estructura o fondo; también puede ocurrir con productos escasos o poco contrastados. El mapa amarillo conserva la señal bruta: esta abstención no detecta ni borra automáticamente esos elementos.

Si la foto es recortada o un contorno alcanza el encuadre, se muestra Solo zona visible y Revisar; un porcentaje alto no certifica el nivel completo. Si se indica un objeto delante se suspende la medición. Si se indica una persona tapando la góndola, se muestra Góndola tapada y se pide otra foto, sin contornos, ocupación ni reposición. La ausencia de detecciones no significa góndola vacía.

En las pruebas conocidas, el superior vacío de Líder Express 030 puede omitirse; en 029 el contorno superior puede quedar demasiado alto. Revisar estos casos y fotos nuevas antes de tomar decisiones operativas. No se evaluó la reserva final de 63 fotos. La validación común de máscaras no mejoró globalmente respecto del padre; la adopción de esta versión fue una decisión visual del usuario con estas limitaciones conocidas.

## Próximo refuerzo

El laboratorio local en http://127.0.0.1:8090 conserva este best.pt como modelo entrenado vigente. Los registros de los ensayos anteriores se conservan; sus checkpoints se retiraron en la limpieza autorizada del 26 de octubre. Las nuevas fotos se reciben en `Datos/V3/Refuerzo/Por_anotar/` dentro del proyecto; deben anotarse, revisarse y agruparse por escena antes de otro afinado. Las tomas relacionadas no son validación independiente.

## Alcance de esta entrega

El manifiesto `modelos.json` conserva el ensayo fuente y el hash exacto de los pesos. Vicente probó correctamente el procedimiento Docker en macOS con la release anterior. V3 conserva el mismo flujo y dependencias, incorporando sus módulos actuales. La ocupación sigue pendiente de calibración. El cuaderno opcional de Colab informa antes de cargar que los archivos se subirán al entorno de Google.
