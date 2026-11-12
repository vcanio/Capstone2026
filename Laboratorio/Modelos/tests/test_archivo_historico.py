"""Registered relocations preserve IDs without accepting arbitrary filesystem escapes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import archivo_historico as archive


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.config-modelo').mkdir()
        self.target = self.root / 'Historico/Experimentos/old'
        self.target.mkdir(parents=True)
        (self.target / 'manifest.json').write_text('{}')
        (self.root / archive.REGISTRY).write_text(json.dumps({'rutas': [
            {'origen': 'Laboratorio/Experimentos/old', 'destino': 'Historico/Experimentos/old'}]}))

    def test_reads_explicit_alias_and_preserves_unmapped_paths(self):
        self.assertEqual(archive.read_path(self.root, 'Experimentos/old/manifest.json'), self.target / 'manifest.json')
        self.assertEqual(archive.read_path(self.root, 'Experimentos/current/manifest.json'), self.root / 'Experimentos/current/manifest.json')

    def test_rejects_traversal_and_unregistered_archive(self):
        for value in ('../secret', '/secret', 'C:/secret', 'Experimentos/old/../secret', 'Experimentos/old2/manifest.json'):
            self.assertIsNone(archive.registered_target(self.root, value))
        self.assertFalse(archive.within(self.root, self.target / 'manifest.json', self.root / 'Datos'))

    def test_registry_cannot_redirect_outside_archive(self):
        (self.root / archive.REGISTRY).write_text(json.dumps({'rutas': [
            {'origen': 'Experimentos/old', 'destino': '../outside'}]}))
        with self.assertRaises(ValueError):
            archive.registered_target(self.root, 'Experimentos/old/manifest.json')

    def test_resolved_escape_is_rejected(self):
        real = Path.resolve
        def redirected(path, *args, **kwargs):
            if path == self.target / 'escape':
                return self.root.parent / 'secret'
            return real(path, *args, **kwargs)
        with patch.object(Path, 'resolve', redirected):
            self.assertIsNone(archive.registered_target(self.root, 'Experimentos/old/escape'))

    def test_docker_mount_alias_requires_same_filesystem_object(self):
        path = self.root / 'Experimentos/old/manifest.json'
        real = Path.resolve
        def mounted(p, *args, **kwargs):
            return Path('/mnt/host/project/old/manifest.json') if p == path else real(p, *args, **kwargs)
        with patch.object(Path, 'resolve', mounted), patch.object(Path, 'samefile', return_value=True):
            self.assertTrue(archive.within(self.root, path, self.root / 'Experimentos'))
        with patch.object(Path, 'resolve', mounted), patch.object(Path, 'samefile', return_value=False):
            self.assertFalse(archive.within(self.root, path, self.root / 'Experimentos'))
