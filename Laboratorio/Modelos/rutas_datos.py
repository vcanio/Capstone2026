"""Rutas actuales de imágenes, con lectura de referencias de ensayos anteriores."""
import re

PROJECT_RENAMES = (('Documentacion/Desarrollo/Notas_Release_Walmart_Vision_Docker_20261021.md', 'Historico/Documentacion/Desarrollo/Notas_Release_Walmart_Vision_Docker_20261021.md'), ('Documentacion/Desarrollo/Implementacion_laboratorio_modelos_20261022.md', 'Historico/Documentacion/Desarrollo/Implementacion_laboratorio_modelos_20261022.md'), ('Documentacion/Desarrollo/Plan_mejora_laboratorio_modelos_20261022.md', 'Historico/Documentacion/Desarrollo/Plan_mejora_laboratorio_modelos_20261022.md'), ('Documentacion/Desarrollo/Notas_Release_Walmart_Vision_20261020.md', 'Historico/Documentacion/Desarrollo/Notas_Release_Walmart_Vision_20261020.md'), ('Documentacion/Desarrollo/Notas_Release_Walmart_Vision_20261022.md', 'Historico/Documentacion/Desarrollo/Notas_Release_Walmart_Vision_20261022.md'), ('Documentacion/Desarrollo/Plan_particion_lider_express_20261016.md', 'Historico/Documentacion/Desarrollo/Plan_particion_lider_express_20261016.md'), ('Documentacion/Desarrollo/Posprocesamiento_contornos_niveles.md', 'Historico/Documentacion/Desarrollo/Posprocesamiento_contornos_niveles.md'), ('Documentacion/Desarrollo/Experimento_YOLO_Paulo_v2.md', 'Historico/Documentacion/Desarrollo/Experimento_YOLO_Paulo_v2.md'), ('Experimentos/v2_base_yolo11n_01_20261020_002800_ec8d', 'Historico/Experimentos/v2_base_yolo11n_01_20261020_002800_ec8d'), ('Experimentos/v2_base_yolo26n_01_20261020_004933_b105', 'Historico/Experimentos/v2_base_yolo26n_01_20261020_004933_b105'), ('Documentacion/Desarrollo/Entrenamiento_niveles_v2.md', 'Historico/Documentacion/Desarrollo/Entrenamiento_niveles_v2.md'), ('Documentacion/Desarrollo/Evolucion_v1_v2.md', 'Historico/Documentacion/Desarrollo/Evolucion_v1_v2.md'), ('Experimentos/YOLO11-1_20261015_013749_f709', 'Historico/Experimentos/YOLO11-1_20261015_013749_f709'), ('Experimentos/YOLO26-1_20261015_021212_c452', 'Historico/Experimentos/YOLO26-1_20261015_021212_c452'), ('Documentacion/Desarrollo/Guia_anotacion.md', 'Historico/Documentacion/Desarrollo/Guia_anotacion.md'), ('Documentacion/Historico', 'Historico/Documentacion'), ('Herramientas/Demo_lite', 'Aplicacion'), ('Experimentos/Contornos', 'Historico/Experimentos/Contornos'), ('reproducibilidad', 'Historico/Reproducibilidad'), ('Herramientas', 'Laboratorio'), ('Experimentos', 'Laboratorio/Experimentos'), )

RENAMES = (
    ('Datos/Equilibrado_v1_20261013', 'Datos/V1/Equilibrado_v1_20261013'),
    ('Datos/Imagenes', 'Datos/V1/Lider'),
    ('Datos/Para_anotar/Originales', 'Datos/V1/Lider'),
    ('Datos/Para_anotar', 'Datos/V1'),
    ('Datos/Pendientes', 'Datos/V2'),
    ('Datos/Evaluacion_final/Reservadas', 'Datos/V1/Reservadas'),
    ('Datos/Fotos_prueba', 'Laboratorio/Experimentos/panel_pruebas/Subidas_panel'),
    ('Datos/Para_probar/Subidas_panel', 'Laboratorio/Experimentos/panel_pruebas/Subidas_panel'),
)


def current_image_path(value):
    """Traducir solo prefijos conocidos; la autorización se hace en el consumidor."""
    if not isinstance(value, str):
        return value
    for previous, current in PROJECT_RENAMES:
        if value == previous or value.startswith(previous + "/"):
            value = current + value[len(previous):]
            break
    for previous, current in RENAMES:
        if value == previous or value.startswith(previous + '/'):
            value = current + value[len(previous):]
            break
    real = re.fullmatch(r'Datos/V1/Equilibrado_v1_20261013/reales/(?:entrenamiento/|validacion/)?REAL_(\d{2})\.jpg', value)
    if real:
        return f'Datos/V1/Lider/lider_{int(real[1]):03}.jpg'
    synthetic = re.fullmatch(r'Datos/V1/Equilibrado_v1_20261013/sinteticas/(?:entrenamiento/)?(EQ_[A-Za-z0-9_]+\.png)', value)
    if synthetic:
        return 'Datos/V1/Sinteticas/' + synthetic[1]
    original = re.fullmatch(r'(Datos/V1/(?:Lider|Reservadas)/)(\d{2})\.jpg', value)
    if original:
        return f'{original[1]}lider_{int(original[2]):03}.jpg'
    return value


def current_inventory_path(value):
    return current_image_path('Datos/' + value).removeprefix('Datos/')


def experiment_parts(value):
    """Componentes lógicos para validar rutas con prefijo de dos directorios."""
    from pathlib import Path
    parts = Path(current_image_path(value)).parts
    if parts[:2] in (("Laboratorio", "Experimentos"), ("Historico", "Experimentos")):
        parts = ("/".join(parts[:2]), *parts[2:])
    return parts
