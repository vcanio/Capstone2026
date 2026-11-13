# Comparar Línea A y franja basal · 12 de noviembre de 2026

Opción local de la **app de revisión, puerto 8095**, solicitada por Vicente.
Línea A sigue predeterminada. La app cliente sigue usando Línea A; el oficial
YOLO, sus pesos y el estimador anterior conservan sus bytes.

## Uso

1. Abrir **Ajustes de análisis → Algoritmo de ocupación**.
2. Elegir **Línea A · actual** y analizar la foto o el lote.
3. Cambiar a **Basal · experimental** y analizar la misma foto o lote.
4. Volver a la otra opción para recuperar su resultado sin repetir el análisis.
   Cada combinación de modelo y algoritmo conserva su resultado, confianza,
   incidencias e historial de revisión. La primera ejecución de cada opción sí
   hace inferencia YOLO; para comparar, mantener modelo, foto y confianza.
5. **Descargar lote** incluye `variantes/` con ambas alternativas y sus revisiones.
   `resultados/` y el resumen principal corresponden a la opción activa.
   La sesión local también conserva las alternativas al volver a abrir el visor.

Si cambia el hash del motor o del algoritmo, el resultado anterior se conserva
como antecedente y se pide reanalizar. Una marca de una opción no aprueba la otra.
La pestaña **Comparar** sigue comparando foto original y resultado seleccionado;
para alternar algoritmos se utiliza el selector de ajustes.

## Qué calcula cada opción

| Opción | Medida | Umbral | Estado |
|---|---|---|---|
| Línea A | Índice visual 0–100: cuerpo vertical y hueco continuo | 52 | Ajuste preliminar existente, sin cambios |
| Basal | Porcentaje de columnas observables con señal respaldada cerca del apoyo | 30 % | Criterio de ensayo independiente, **sin calibrar** |

Basal reutiliza Canny, gradiente, color, textura y exclusión estructural de rieles.
La franja se calcula entre el 65 % y el 95 % de la altura local de cada columna
de la máscara erosionada, en la resolución de la grilla. No se reemplazan los
contornos YOLO por rectángulos. El muestreo vertical es de aproximadamente 8 px
en la imagen escalada; el detector de rieles mantiene sus parámetros originales.

Se exige al menos 50 % de observación por celda, dos filas observadas y 60 % de
la banda observada por columna. Dos filas con señal y al menos 35 % de la parte
observada respaldan una columna. Se conservan columnas estrechas respaldadas;
no se borran solo por tener vecinas vacías. Los huecos conocidos mantienen sus
posiciones y no se unen atravesando columnas desconocidas.

La decisión se basa en cobertura horizontal, sin penalización por altura vacía.
Se pide revisión si hay menos de tres columnas conocidas, menos de 75 % del ancho
observable o si la región desconocida podría cambiar la decisión frente al umbral.
El mayor hueco se conserva como diagnóstico, sin limitar el resultado principal.
Las zonas junto al encuadre siguen requiriendo revisión.

## Límites y comprobaciones

Esto es una candidata para desarrollo, no una adopción ni una mejora de precisión
demostrada. El 30 % no deriva de la calibración de Línea A. El porcentaje basal no
mide stock físico, profundidad, volumen ni cantidad de productos. La máscara de
observación excluye estructuras detectadas: **no detecta todas las oclusiones**.
Un cartel, una bandeja o un producto confundido con el fondo aún pueden fallar.

En la prueba funcional sobre `lider_2_122_0_original.jpg`, confirmada como train
en la partición vigente, ambas rutas devolvieron seis contornos idénticos. Línea A
dio seis suficientes; basal dio dos suficientes y cuatro revisiones por cobertura
observable insuficiente tras excluir estructuras. Se conserva esa limitación;
no se ajustaron los umbrales para hacer pasar esa foto ni se usó el test reservado.

Las pruebas automáticas cubren producto bajo/alto, vacío, franja fina, regiones
desconocidas, contorno inclinado, producto estrecho, conservación del cálculo
original, API, selección, sesiones y ZIP. No equivalen a evaluación de precisión.

Recibos locales: `Datos/Registros/Ocupacion/comparacion_basal_20261112/`.
La publicación y los ZIP existentes permanecen intactos.
