# Trabajar en equipo · 11/11/2026

Repositorio compartido: https://github.com/vcanio/Capstone2026. Cada persona usa su propia copia y cuenta. No compartir contraseñas ni tokens.

## Código y cambios

Actualizar main, crear rama, editar, ejecutar las pruebas pertinentes, hacer commit, push y abrir un pull request para revisión. Quien mantiene la entrega verifica el código integrado y publica un tag y ZIP nuevos. Los acuerdos de trabajo no acreditan permisos de GitHub ya configurados.

| Componente | Ruta actual |
|---|---|
| Cliente: alertas, revisión humana y CSV | `Aplicacion_Cliente/` |
| Equipo, motor y ocupación portable | `Aplicacion/` |
| Panel, selección, preparación y entrenamiento | `Laboratorio/Modelos/` |
| Prototipo de ocupación y etiquetador | `Laboratorio/Ocupacion/` |
| Datos, integridad y conexión externa | `Laboratorio/Datos/` |
| Empaquetado y auditoría pública | `Laboratorio/Reproducibilidad/` |
| Guías y evidencia resumida | `Documentacion/` |

Modificar los originales con control de versiones. Los experimentos nuevos reciben un ID nuevo; no reemplazan ensayos, etiquetas o manifiestos congelados.

## Iniciar una copia

```powershell
git clone https://github.com/vcanio/Capstone2026.git
cd Capstone2026
git config user.name "TU NOMBRE"
git config user.email "TU_CORREO_DE_GITHUB"
```

Para usar las apps en Windows, abrir `Aplicacion_Cliente/iniciar_cliente.cmd` o `Aplicacion/iniciar.cmd`; el primer inicio descarga dependencias. El clon incluye un solo peso oficial operativo. Para Docker y desarrollo, consultar [Instalación](Replicar_proyecto.md).

## Datos y entrenamiento

Fotografías privadas, sesiones, configuraciones, entornos y respaldos quedan fuera de GitHub. El repositorio no es un respaldo completo del proyecto local. Los resúmenes públicos no sustituyen los activos privados necesarios para repetir un ensayo.

Las fotos cargadas en las apps no se incorporan al entrenamiento. Solo Vicente inicia un futuro entrenamiento desde el panel con un plan nuevo a partir del cierre oficial adoptado. No reutilizar el test reservado para ajustes ni convertir predicciones en anotaciones humanas.

Publicar una distribución requiere pruebas, licencia, avisos, fuente correspondiente y verificación de la descarga. Mantener las releases anteriores con sus activos. [Procedimiento de publicación](Publicar_GitHub.md) · [Guía anterior conservada](../../Historico/Documentacion/Desarrollo/Trabajo_en_equipo_antes_alineacion_20261111.md).
