# App cliente · diseño aplicado el 11/11/2026

> Nota de vigencia: el cliente recibió después el flujo de alertas y revisión humana y la limpieza definitiva. Véase [estado actual del cliente](Cliente_alertas_20261111.md). Las comprobaciones siguientes corresponden a la intervención fechada que describen.

Petición de Vicente: aplicar la captura `Screenshot 2026-11-11 011339.png` a la
aplicación cliente y mejorar su logo, teniendo presente que los contornos dependen
del modelo. Trabajo local; sin publicación ni cambios en la app de revisión.

## Implementación

- Cabecera azul, acción de carga amarilla, filtros compactos y tres columnas.
- Cola con miniaturas y estado; foto central completa; plan de niveles descendente.
- Logo SVG original con esquinas de encuadre y estantes; cabecera, vacío y favicon
  comparten `Aplicacion_Cliente/logo.svg`.
- SVG de resultados basado en las coordenadas `display_polygon` de cada detección.
  Los colores y etiquetas reflejan el diagnóstico y el índice devueltos por el motor.
  No se fija el número de niveles ni se copian los contornos de la referencia.
- Verificación rápida Sin verificar / Correcto / Repuesto. Diagnóstico y opciones
  adicionales en Detalle; se conserva el resultado original de la foto.
- Comparación y original, carga/cámara, guardado IndexedDB, CSV total y filtrado,
  tema claro y limpieza reversible conservados. Controles secundarios en Más opciones.
- Móvil con recorrido horizontal y plan bajo el visor, sin desbordamiento del documento.
- Empaquetador actualizado para incluir el SVG en futuras entregas. No se creó ni
  publicó una nueva release o ZIP de distribución.

## Comprobaciones

- Nueve pruebas existentes de cliente HTTP/diagnóstico aprobadas; se añadió al
  chequeo de interfaz la comprobación de la ruta y los bytes del logo.
- Prueba de empaquetado conjunto aprobada, incluida comprobación del SVG del cliente.
- JavaScript válido mediante `node --check`.
- Flujo real del catálogo de cuatro demos de desarrollo analizado con el motor
  oficial. No se cargó la reserva de Ohiggins 3 ni test histórico.
- Browser: reposición sin modificar puntaje; confirmación persistente tras recarga;
  vista original sin SVG; comparación; filtros sin coincidencias; diagnóstico
  desplegable y cambio de tema.
- CSV descargado: 21 niveles, 11 columnas, estructura íntegra UTF-8 BOM con punto y coma.
- Detector de diseño ejecutado una vez; se corrigieron contraste de botones azules
  y tamaños de texto señalados. Esto no constituye certificación de accesibilidad.
- Revisión visual independiente `impeccable-finish-reviewer`: disposición **ship**,
  sin correcciones materiales. La revisión cubrió interfaz y capturas, no backend.

## Evidencias

Capturas en `.impeccable/review/` desde la raíz del proyecto:

- `cliente-1920.jpg`: escritorio 1920 × 1080, composición de referencia.
- `cliente-desktop.jpg`: escritorio 1440 × 1000.
- `cliente-light.jpg`: tema claro 1440 × 1000.
- `cliente-mobile.jpg`: página completa de 380 × 2083; viewport configurado
  de 390 × 844, con barra de desplazamiento del navegador.

Respaldo anterior de HTML y servidor en `.tmp/cliente_diseno_20261111/`.
Documentación visual limitada a `Aplicacion_Cliente/DESIGN.md` y su sidecar.
No se modificaron CVAT, pesos, particiones, umbral 52 ni implementación de ocupación.
