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
    def test_packaging_keeps_summaries_and_skips_local_generated_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            checkout = Path(temporary) / 'checkout'
            root.mkdir()
            checkout.mkdir()
            public = ['Documentacion/Evidencias/verificacion.json',
                      'Documentacion/Historico.md',
                      'Datos/Registros/Particiones/lote/particion.json']
            local = ['Datos/Registros/Particiones/lote/respaldo_registros/manifest.json',
                     'Documentacion/Evidencias/pruebas_20261021.log',
                     'Documentacion/Evidencias/consulta_github_20261021.json',
                     'Documentacion/Evidencias/otro_corte/pruebas.log',
                     'Documentacion/Evidencias/otro_corte/consulta_github_20261022.json']
            for name in ['README.md', '.gitignore', '.gitattributes', '.dockerignore'] + public + local:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{}' if path.suffix == '.json' else 'Referencia de prueba', encoding='utf-8')
            with patch.object(packaging, 'ROOT', root), patch.object(
                    packaging.subprocess, 'run',
                    return_value=SimpleNamespace(returncode=1, stdout=b'', stderr=b'')):
                copied = packaging.copy_code('git', checkout)
                evidence = packaging.files_under(root / 'Documentacion')
            self.assertTrue(set(public).issubset(copied))
            for name in local:
                self.assertTrue((root / name).is_file())
                self.assertFalse((checkout / name).exists())
                self.assertNotIn(root / name, evidence)

    def test_audit_rejects_generated_files_forced_into_git(self):
        for name in ('Datos/Registros/Particiones/lote/respaldo_registros/manifest.json',
                     'Documentacion/Evidencias/pruebas_20261021.log',
                     'Documentacion/Evidencias/consulta_github_20261021.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / 'reproducibilidad').mkdir()
                (root / 'reproducibilidad/artefactos.json').write_text('{"packages": {}}', encoding='utf-8')
                path = root / name
                path.parent.mkdir(parents=True)
                path.write_text('{}', encoding='utf-8')
                subprocess.run(['git', '-C', str(root), 'init', '--quiet'], check=True, capture_output=True)
                subprocess.run(['git', '-C', str(root), 'add', '-f', '--', name],
                               check=True, capture_output=True)
                with self.assertRaisesRegex(ValueError, 'Archivo privado visible para Git:'):
                    publication.verify(root)

    def test_public_summaries_and_required_academic_files_are_allowed(self):
        for name in ('Fase 1/Evidencias individuales/diario.docx',
                     'Fase 1/Evidencias grupales/evaluacion.xlsx',
                     'Documentacion/Evidencias/verificacion_informe_20261020.json',
                     'Datos/Registros/Particiones/lote/particion.json',
                     'Datos/Registros/Particiones/lote/fuentes/tarea_19.json'):
            with self.subTest(name=name):
                self.assertFalse(publication.local_only(name))

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
