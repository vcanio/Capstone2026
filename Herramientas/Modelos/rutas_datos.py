"""Rutas actuales de imágenes, con lectura de referencias de ensayos anteriores."""
import re

RENAMES = (
    ('Datos/Equilibrado_v1_20261013', 'Datos/V1/Equilibrado_v1_20261013'),
    ('Datos/Imagenes', 'Datos/V1/Lider'),
    ('Datos/Para_anotar/Originales', 'Datos/V1/Lider'),
    ('Datos/Para_anotar', 'Datos/V1'),
    ('Datos/Pendientes', 'Datos/V2'),
    ('Datos/Evaluacion_final/Reservadas', 'Datos/V1/Reservadas'),
    ('Datos/Fotos_prueba', 'Experimentos/panel_pruebas/Subidas_panel'),
    ('Datos/Para_probar/Subidas_panel', 'Experimentos/panel_pruebas/Subidas_panel'),
)


def current_image_path(value):
    """Traducir solo prefijos conocidos; la autorización se hace en el consumidor."""
    if not isinstance(value, str):
        return value
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
