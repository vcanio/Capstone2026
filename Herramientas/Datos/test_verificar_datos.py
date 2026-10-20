"""Regresiones de integridad y del estado pendiente con lotes pequenos."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from verificar_datos import verify


class DataAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = self.root / 'Datos/V2/local_20261016'
        self.base.mkdir(parents=True)
        image = self.base / 'imagenes/local_001.jpg'
        image.parent.mkdir()
        image.write_bytes(b'foto pendiente de prueba')
        entry = dict(imagen_id='local_001', archivo='imagenes/local_001.jpg',
                     sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                     uso='pendiente', estado_anotacion='sin_anotar')
        with (self.base / 'inventario.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=entry.keys())
            writer.writeheader()
            writer.writerow(entry)
        self.manifest = dict(imagenes=1, estado='pendiente_de_reparto', cvat=None,
                             aprobado_entrenamiento=False, directorio_imagenes='imagenes',
                             reparto=dict(anotacion=0, pruebas=0, evaluacion_final=0, pendientes=1))
        self.write('Datos/V2/local_20261016/manifest.json', self.manifest)
        self.write('Datos/Registros/lotes.json', dict(schema_version=1, lotes=[dict(
            id='local_20261016', imagenes=1, estado='pendiente_de_reparto',
            inventario='Datos/V2/local_20261016/inventario.csv',
            base_archivos='Datos/V2/local_20261016', id_columna='imagen_id',
            manifest='Datos/V2/local_20261016/manifest.json')]))
        # Un paquete vacio permite aislar la auditoria del lote pendiente.
        self.write('Datos/V1/paquete/manifest.json', dict(imagenes=[]))
        self.write('Datos/Registros/reserva_evaluacion.json', dict(groups=[], image_ids=[]))
        self.write('Datos/Registros/dataset_activo.json', dict(
            manifest='Datos/V1/paquete/manifest.json', imagenes=0,
            version_modelos_ruta='Datos/Registros/Versiones_modelos/version/version.json',
            version_modelos='version', imagenes_activas=0))
        snapshot = self.write('Datos/Registros/Versiones_modelos/version/snapshot_cvat.json', {})
        partition = self.write('Datos/Registros/Versiones_modelos/version/particion.json', {})
        self.write('Datos/Registros/Versiones_modelos/version/version.json', dict(
            id='version', report=dict(imagenes=[]),
            snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            partition_sha256=hashlib.sha256(partition.read_bytes()).hexdigest()))

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def test_valid_pending_lot_passes_without_modifying_image(self):
        path = self.base / 'imagenes/local_001.jpg'
        before = path.read_bytes()
        self.assertEqual(verify(self.root)['fotos_pendientes'], 1)
        self.assertEqual(path.read_bytes(), before)

    def test_changed_image_is_rejected(self):
        (self.base / 'imagenes/local_001.jpg').write_bytes(b'contenido cambiado')
        with self.assertRaisesRegex(ValueError, 'SHA-256 distinto'):
            verify(self.root)

    def test_pending_lot_cannot_silently_assign_training_permission(self):
        self.manifest['aprobado_entrenamiento'] = True
        self.write('Datos/V2/local_20261016/manifest.json', self.manifest)
        with self.assertRaisesRegex(ValueError, 'habilitado para CVAT o entrenamiento'):
            verify(self.root)

    def test_unregistered_image_is_rejected(self):
        (self.base / 'imagenes/otra.jpg').write_bytes(b'foto sin registro')
        with self.assertRaisesRegex(ValueError, 'sin registrar o faltantes'):
            verify(self.root)


if __name__ == '__main__':
    unittest.main()
