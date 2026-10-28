# Walmart Vision · V3

Interfaz local simplificada del 26 de octubre de 2026, sobre el modelo cerrado e integrado por decisión de Vicente el 25. Incluye únicamente el `best.pt` del afinado de papeles, huevos y superiores vacíos. El historial de los modelos anteriores se conserva en la documentación del proyecto.

## Usar la aplicación

En Windows, extraer todo el ZIP y abrir `iniciar.cmd`. En Docker, ejecutar `docker compose up --build -d --wait` desde la carpeta extraída. Abrir http://127.0.0.1:8095. La primera preparación puede requerir conexión para instalar dependencias; después la inferencia es local. Las fotos no se incorporan al entrenamiento. La sesión del lote, incluidas las fotos, se guarda en el navegador de este equipo para recuperarla; puede eliminarse desde la aplicación.

1. Seleccionar una foto JPG, PNG o WebP de hasta 15 MB.
   También puedes elegir **Tomar foto con guía** y permitir el acceso a la cámara. El marco y las líneas ayudan a encuadrar; no son detecciones ni se incorporan a la foto. Revisa la imagen antes de analizarla. La cámara necesita una conexión segura HTTPS o acceso desde el propio equipo (localhost).
2. El análisis usa automáticamente el modelo vigente, detección de niveles y bordes, con confianza inicial 0,60 ajustable desde 0,40.
3. Pulsar Analizar foto. Revisar contornos, ocupación estimada, alcance y avisos. Original, Niveles, Bordes y Comparar permiten comprobar el resultado.

## Fotografías frontales

**Para usar esta versión, toma fotos frontales o casi frontales de la góndola.** Sitúate frente al tramo, mantén la cámara nivelada y procura que se vean sus dos extremos y las superficies de apoyo. Evita tomas desde un costado, desde muy arriba o abajo, panorámicas deformadas, desenfoque y reflejos fuertes. Si el mueble es largo, utiliza varias tomas frontales de tramos completos.

La perspectiva oblicua cambia las alturas y anchuras aparentes, oculta huecos detrás de los productos y puede desplazar las máscaras. El algoritmo estima una proporción de la imagen, sin reconstruir el volumen ni corregir automáticamente la perspectiva. Una foto frontal ayuda, pero no garantiza una detección correcta: revisa siempre los contornos y la visibilidad. No hay un ángulo máximo validado ni un detector automático que certifique que la toma sea frontal.

## Criterio de nivel y mediana

Un nivel es el área útil completa donde pueden existir productos y huecos, apoyada sobre la repisa, por encima del portaprecio. Se respetan los límites interiores y la cubierta física cuando existe; no se ajusta a los envases ni solo a la franja frontal. Un nivel vacío sigue siendo un nivel.

Si el superior no tiene un techo claro, las anotaciones usan la mediana de las alturas inferiores del mismo tramo, medida en el centro y proyectada desde el apoyo sobre el portaprecio. Por ejemplo, 190, 195, 210 y 220 píxeles producen 202,5 píxeles. Es una convención para mantener el mismo criterio en originales y variantes llenas o vacías. Si la proyección sale de la foto, se recorta y marca parcial. La app conserva las máscaras de YOLO: no recalcula ni fuerza esa mediana durante la predicción.

## Interpretar el resultado

YOLO V3 predice una sola clase: Nivel. Conserva las máscaras del modelo; no impone una mediana ni inventa niveles omitidos. La confianza no es ocupación.

Los bordes son cambios de intensidad de la foto, distintos del contorno del nivel. Se combinan con gradiente, color y textura por celdas dentro de la máscara. El mapa fucsia es esa señal combinada, no producto confirmado. La lectura estima qué parte del frente tiene señal con respaldo de bordes o textura, sin penalizar el espacio libre sobre productos bajos. Se asume lleno detrás del producto visible. Por debajo del 30 % muestra Reponer y desde el 30 %, Suficiente, cuando las reglas permiten una lectura. El cálculo 70/30 anterior se conserva como diagnóstico. La cobertura es experimental, no está calibrada ni identifica productos de manera fiable.

Cuando la señal se concentra arriba, o queda en la periferia sin suficiente respaldo central e inferior, se muestra Revisar · señal ambigua, sin porcentaje ni decisión de reposición. Puede proceder de cartelería, estructura o fondo; también puede ocurrir con productos escasos o poco contrastados. El mapa fucsia conserva la señal bruta: esta abstención no detecta ni borra automáticamente esos elementos.

Si un contorno alcanza el encuadre, se muestra Solo zona visible y Revisar; un porcentaje alto no certifica el nivel completo. La app no detecta automáticamente personas ni obstáculos: revisa las zonas tapadas o fuera del encuadre. La ausencia de detecciones no significa góndola vacía.

En las pruebas conocidas, el superior vacío de Líder Express 030 puede omitirse; en 029 el contorno superior puede quedar demasiado alto. Revisar estos casos y fotos nuevas antes de tomar decisiones operativas. No se evaluó la reserva final de 63 fotos. La validación común de máscaras no mejoró globalmente respecto del padre; la adopción de esta versión fue una decisión visual del usuario con estas limitaciones conocidas.

## Próximo refuerzo

El laboratorio local en http://127.0.0.1:8090 conserva este best.pt como modelo entrenado vigente. Los registros de los ensayos anteriores se conservan; sus checkpoints se retiraron en la limpieza autorizada del 26 de octubre. Las nuevas fotos se reciben en `Datos/V3/Refuerzo/Por_anotar/` dentro del proyecto; deben anotarse, revisarse y agruparse por escena antes de otro afinado. Las tomas relacionadas no son validación independiente.

## Alcance de esta entrega

El manifiesto `modelos.json` conserva el ensayo fuente y el hash exacto de los pesos. Vicente probó correctamente el procedimiento Docker en macOS con la release anterior. V3 conserva el mismo flujo y dependencias, incorporando sus módulos actuales. La ocupación sigue pendiente de calibración. El cuaderno opcional de Colab informa antes de cargar que los archivos se subirán al entorno de Google.
