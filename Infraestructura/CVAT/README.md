# Conexión opcional a CVAT

La inferencia y los ensayos congelados funcionan sin CVAT. Para traer anotaciones
nuevas, consultar [Replicar el proyecto](../../Documentacion/Replicar_proyecto.md).

Cada compañero usa su propia cuenta. La URL se configura en
Infraestructura/Docker/.env.modelos y las credenciales en
Infraestructura/CVAT/acceso_local.json, ambos ignorados por Git. La plantilla
sin credenciales está en Infraestructura/Docker/acceso_cvat.example.json.

El Compose opcional compose.modelos.cvat.yml monta ese archivo como solo lectura.
El inicio Windows admite -ConCvat. El repositorio no distribuye usuarios,
contraseñas, claves Tailscale ni volúmenes de la instalación original.

La guía de [migración privada](../Migracion.md) describe una operación distinta:
trasladar toda la instalación del anfitrión. Ese respaldo no es una Release pública.
