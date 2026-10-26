# V3: áreas útiles de niveles

El modelo V3 aprende **Nivel**: el área útil sobre la superficie de apoyo de cada repisa. La ocupación se estima después, mediante un algoritmo separado que sigue siendo experimental.

El catálogo vigente contiene **469 imágenes**, con **337 train / 69 val / 63 test**. Una imagen train está desactivada. El último afinado utiliza una selección de **113 fotos**, con refuerzos de superiores vacíos, papeles y huevos, más repaso.

## Criterio geométrico

La base de cada nivel se coloca en la superficie de apoyo, sobre el portaprecio. En superiores abiertos, sin techo físico claro, la anotación utiliza la mediana de las alturas de los inferiores del mismo tramo. Los recortes se marcan como parciales.

Es un criterio de anotación: la app conserva las máscaras del modelo y no impone la mediana durante la predicción. Las marcas de oclusión tampoco producen una clasificación automática de visibilidad.

[Criterio V3](../../Documentacion/Desarrollo/Criterio_V3_niveles.md) · [Regla de mediana](../../Documentacion/Desarrollo/Regla_nivel_superior_mediana_V3.md)

## Referencias vigentes

[Datos y partición](../README.md) · [Registros](../Registros/README.md) · [Modelo actual](../../Documentacion/Modelo_V3_actual.md) · [Resumen numérico](../../Documentacion/Estado_V3_actual.json)

Las fuentes reutilizadas conservan sus rutas originales. Los inventarios históricos documentan su procedencia; no son conjuntos adicionales que deban sumarse al catálogo actual.
