import unittest
from unittest.mock import patch

import panel_modelos as panel


class VisibilidadPanelTests(unittest.TestCase):
    def test_iniciar_validacion_de_visibilidad_no_lee_catalogo_historico(self):
        with patch.object(panel, 'ACTIVE', None), patch.object(panel, 'catalog') as catalog, \
             patch.object(panel, 'validate', side_effect=ValueError('validación controlada')) as validate:
            with self.assertRaisesRegex(ValueError, 'validación controlada'):
                panel.launch({'pipeline': 'visibilidad_foto_v1', 'action': 'train'})
            catalog.assert_not_called()
            validate.assert_called_once_with({'pipeline': 'visibilidad_foto_v1', 'action': 'train'}, {})

    def test_iniciar_segmentacion_v3_no_lee_catalogo_historico(self):
        config = {'pipeline': panel.training_v3.CRITERION, 'action': 'train'}
        with patch.object(panel, 'ACTIVE', None), patch.object(panel, 'catalog') as catalog, \
             patch.object(panel, 'validate', side_effect=ValueError('validación controlada')) as validate:
            with self.assertRaisesRegex(ValueError, 'validación controlada'):
                panel.launch(config)
            catalog.assert_not_called()
            validate.assert_called_once_with(config, {})

    def test_sin_revision_no_se_prepara_trabajo(self):
        with patch.object(panel.datasets, 'CvatReader'), \
             patch.object(panel.visibility_review, 'collect', return_value={'images': []}), \
             patch.object(panel.visibility_training, 'prepare', side_effect=ValueError('Revisión pendiente')):
            with self.assertRaisesRegex(ValueError, 'Revisión pendiente'):
                panel.validate({'pipeline': 'visibilidad_foto_v1', 'action': 'train'}, {})

    def test_configuracion_separada_del_localizador(self):
        snapshot = {'images': [{'name': 'ejemplo'}]}
        with patch.object(panel.datasets, 'CvatReader'), \
             patch.object(panel.visibility_review, 'collect', return_value=snapshot), \
             patch.object(panel.visibility_training, 'prepare'):
            result = panel.validate({'pipeline': 'visibilidad_foto_v1', 'action': 'train'}, {})
        self.assertEqual(result['source_kind'], 'visibility_review')
        self.assertEqual((result['epochs'], result['batch'], result['imgsz']), (40, 2, 640))
        self.assertIs(result['_revision'], snapshot)
        self.assertNotIn('model', result)


if __name__ == '__main__':
    unittest.main()
