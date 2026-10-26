import os
from pathlib import Path
import sys
import tempfile
import unittest
import threading
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Modelos'))
import datos_modelos
import panel_modelos


class OptionalCvatTests(unittest.TestCase):
    def test_disabled_import_has_a_clear_http_response(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), panel_modelos.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with patch.dict(os.environ, {'CVAT_ENABLED': 'false'}), self.assertRaises(HTTPError) as result:
                urlopen(f'http://127.0.0.1:{server.server_port}/api/datasets/sources')
            self.assertEqual(result.exception.code, 400)
            self.assertIn('deshabilitado', result.exception.read().decode())
        finally:
            server.shutdown()
            server.server_close()

    def test_disabled_cvat_never_reads_credentials_or_connects(self):
        with patch.dict(os.environ, {'CVAT_ENABLED': 'false'}), patch.object(datos_modelos, 'read') as read:
            with self.assertRaisesRegex(ValueError, 'deshabilitado'):
                datos_modelos.CvatReader()
            read.assert_not_called()

    def test_missing_credentials_have_an_actionable_error(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = str(Path(temp) / 'missing.json')
            with patch.dict(os.environ, {'CVAT_ENABLED': 'true', 'CVAT_ACCESS_FILE': missing}):
                with self.assertRaisesRegex(ValueError, 'archivo privado'):
                    datos_modelos.CvatReader()
