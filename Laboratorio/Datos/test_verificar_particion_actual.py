"""Schema 4 development checks must not read or assert the external final test."""
from unittest import TestCase
from unittest.mock import patch
import verificar_particion_v3 as verifier


class CurrentPartitionVerificationTests(TestCase):
    def test_development_partition_does_not_load_legacy_test(self):
        part = {'schema_version': 6, 'imagenes': [], 'resumen': {}}
        with patch.object(verifier.prep, 'partition_reference', return_value='active'), \
             patch.object(verifier.prep, 'partition', return_value=part) as load:
            result = verifier.verify()
        load.assert_called_once_with(verifier.ROOT, 'active')
        self.assertEqual(result['test_images'], 0)
        self.assertIsNone(result['test_preserved'])
        self.assertFalse(result['external_test_checked'])
