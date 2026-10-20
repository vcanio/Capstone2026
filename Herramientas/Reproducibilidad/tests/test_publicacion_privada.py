"""El material privado no debe copiarse ni aceptarse en una publicación."""
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import empaquetar_publicacion as packaging
import verificar_publicacion as publication


class PrivateContextTests(unittest.TestCase):
    def test_packaging_excludes_context_even_without_ignore_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            checkout = Path(temporary) / 'checkout'
            root.mkdir()
            checkout.mkdir()
            for name in ('README.md', '.gitignore', '.gitattributes', '.dockerignore'):
                (root / name).write_text('', encoding='utf-8')
            (root / 'Contexto').mkdir()
            private = root / 'Contexto/reunion.txt'
            private.write_text('Referencia privada de prueba', encoding='utf-8')
            with patch.object(packaging, 'ROOT', root), patch.object(
                    packaging.subprocess, 'run',
                    return_value=SimpleNamespace(returncode=1, stdout=b'', stderr=b'')):
                copied = packaging.copy_code('git', checkout)
            self.assertIn('README.md', copied)
            self.assertFalse((checkout / 'Contexto').exists())
            self.assertEqual(private.read_text(encoding='utf-8'), 'Referencia privada de prueba')

    def test_audit_rejects_context_forced_into_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'reproducibilidad').mkdir()
            (root / 'reproducibilidad/artefactos.json').write_text(
                '{"packages": {}}', encoding='utf-8')
            (root / '.gitignore').write_text('/Contexto/\n', encoding='utf-8')
            (root / 'Contexto').mkdir()
            (root / 'Contexto/reunion.txt').write_text('Referencia privada de prueba', encoding='utf-8')
            subprocess.run(['git', '-C', str(root), 'init', '--quiet'], check=True, capture_output=True)
            subprocess.run(['git', '-C', str(root), 'add', '-f', '--', 'Contexto/reunion.txt'],
                           check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, 'Archivo privado visible para Git: Contexto/'):
                publication.verify(root)


if __name__ == '__main__':
    unittest.main()
