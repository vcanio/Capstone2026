"""Portabilidad del entorno y conexión a CVAT detrás del proxy local."""
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import datos_modelos as datasets
import piloto_modulos as pilot


class RuntimeTests(unittest.TestCase):
    def test_font_can_be_supplied_without_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            font = Path(directory) / 'font.ttf'
            font.touch()
            with patch.dict(os.environ, {'MODEL_FONT': str(font)}):
                self.assertEqual(pilot.font_path(), font)

    def test_cpu_and_gpu_selection(self):
        for available, expected in ((False, 'cpu'), (True, 0)):
            torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: available))
            with patch.dict('sys.modules', {'torch': torch}):
                self.assertEqual(pilot.compute_device(), expected)

    def test_cvat_proxy_host_and_token_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            access = Path(directory) / 'access.json'
            access.write_text(json.dumps({'username': 'fixture', 'password': 'fixture'}))
            from io import BytesIO
            with patch.dict(os.environ, {'CVAT_ACCESS_FILE': str(access),
                                         'CVAT_HOST_HEADER': 'localhost:8082'}), \
                 patch.object(datasets, 'CVAT', 'http://host.docker.internal:8082/api'), \
                 patch.object(datasets, 'urlopen', side_effect=[BytesIO(b'{"key":"test-token"}'),
                                                               BytesIO(b'{"id":27}')]) as request:
                reader = datasets.CvatReader()
                self.assertEqual(reader.request('/jobs/27')['id'], 27)
                login, job = [call.args[0] for call in request.call_args_list]
                self.assertEqual(login.full_url, 'http://host.docker.internal:8082/api/auth/login')
                self.assertEqual(job.get_header('Host'), 'localhost:8082')
                self.assertEqual(job.get_header('Authorization'), 'Token test-token')
