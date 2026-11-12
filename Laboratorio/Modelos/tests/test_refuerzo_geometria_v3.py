"""Guardas del refuerzo y tolerancia exclusivamente numérica en coordenadas."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
import preparacion_v3 as p
import refuerzo_geometria_v3 as g
import entrenamiento_v3 as t
from test_preparacion_v3 import fixture


class RefuerzoGeometryTests(unittest.TestCase):
    def test_scene_matching_counts_duplicate_as_false_positive(self):
        from shapely.geometry import box
        from evaluar_escenas_refuerzo_v3 import match_polygons
        result=match_polygons([box(0,0,10,10),box(0,20,10,30)],
                              [box(0,0,10,10),box(0,0,10,10)])
        self.assertEqual((result['tp'],result['fp'],result['fn']),(1,1,1))
        self.assertTrue(result['exact_count'])

    def test_roundoff_is_normalized_without_mutating_cvat_points(self):
        points=[-2.2737367544323206e-13,1,99,1,99,99,0,99]
        original=points[:]
        self.assertTrue(p.polygon_ok(points,100,100))
        self.assertEqual(p.normalized_points(points,100,100)[0],0)
        self.assertEqual(points,original)
        self.assertTrue(t.labels_text({'points':points,'width':100,'height':100,'shapes':[{'points':points}]}).startswith('0 0 '))

    def test_actual_out_of_frame_is_rejected(self):
        points=[-.001,1,99,1,99,99,0,99]
        self.assertFalse(p.polygon_ok(points,100,100))
        with self.assertRaises(ValueError):p.normalized_points(points,100,100)

    def test_documented_exclusion_is_not_a_negative(self):
        part,snapshot=fixture()
        part['imagenes'][0]['preparation_exclusion']='Retirada a propósito por el usuario.'
        report=p.analyze(part,snapshot)
        image=report['images'][0]
        self.assertFalse(image['eligible'])
        self.assertEqual(len(image['shapes']),1)
        self.assertIn('exclusion_documentada',[x['code'] for x in image['issues']])

    def test_selection_rejects_missing_validation_or_changed_parent(self):
        part={'plan_path':'plan.json','plan_sha256':'p'}
        plan={'initial_model':'best.pt','initial_model_sha256':'m','selected_train':['a'],'selected_val':['b']}
        value={'plan_sha256':'p','required_initial_model':'best.pt','required_initial_model_sha256':'m'}
        images=[{'name':'a','split':'train'},{'name':'b','split':'val'}]
        with patch.object(p,'partition',return_value=part),patch.object(p,'read',return_value=plan):
            self.assertEqual(g.choose(Path('.'),{'partition_path':'p'},images,value),(['a'],[]))
            with self.assertRaises(ValueError):g.choose(Path('.'),{'partition_path':'p'},images[:1],value)
            with self.assertRaises(ValueError):g.choose(Path('.'),{'partition_path':'p'},images,{**value,'required_initial_model_sha256':'changed'})

if __name__=='__main__':unittest.main()
