# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class MarkerLogicTests(unittest.TestCase):
    def test_overlay_is_active_only_with_vehicle_scene_and_no_covering_view(self):
        from wotstat_spotting_points.marker_logic import isOverlaySceneActive

        self.assertTrue(isOverlaySceneActive(True, False))
        self.assertFalse(isOverlaySceneActive(True, True))
        self.assertFalse(isOverlaySceneActive(False, False))

    def test_coincident_static_and_moving_gun_points_are_merged(self):
        from wotstat_spotting_points.marker_logic import buildMarkerData
        mask = [
            (0, 0, -2), (0, 0, 2), (-1, 1, 0), (1, 1, 0),
            (0, 2, 1), (0, 3, 0), (0, 2, 1),
        ]
        spots = [(0, 3, 0), (0, 2, 1)]

        markers = buildMarkerData(mask, spots, 'ru')

        self.assertEqual([marker.id for marker in markers],
                         ['rear', 'front', 'left', 'right',
                          'top', 'gunMoving'])
        self.assertEqual(markers[-1].label,
                         u'Орудийная обзорно-габаритная')

    def test_separated_static_gun_point_gets_its_own_marker(self):
        from wotstat_spotting_points.marker_logic import buildMarkerData
        mask = [
            (0, 0, -2), (0, 0, 2), (-1, 1, 0), (1, 1, 0),
            (0, 2, 1), (0, 3, 0), (1, 2, 1),
        ]
        spots = [(0, 3, 0), (1, 2, 1)]

        markers = buildMarkerData(mask, spots, 'ru')

        self.assertEqual([marker.id for marker in markers],
                         ['rear', 'front', 'left', 'right', 'gunStatic',
                          'top', 'gunMoving'])

    def test_overlay_data_requests_callouts_for_every_marker(self):
        from wotstat_spotting_points.marker_logic import (
            buildOverlayData, MarkerData)
        markers = [
            MarkerData('front', (0, 0, 0), u'Передняя'),
            MarkerData('rear', (0, 0, 0), u'Задняя'),
            MarkerData('left', (0, 0, 0), u'Левая'),
        ]

        payload = buildOverlayData(markers, 'ru')

        self.assertEqual([item['id'] for item in payload],
                         ['front', 'rear', 'left'])
        self.assertTrue(all(item['showLabel'] for item in payload))
        self.assertEqual(payload[0]['tooltipTitle'],
                         u'Передняя габаритная')
        self.assertIn(u'передней грани', payload[0]['tooltipBody'])

    def test_merged_gun_point_uses_separate_tooltip_copy(self):
        from wotstat_spotting_points.marker_logic import (
            buildOverlayData, MarkerData)

        merged = buildOverlayData([
            MarkerData('gunMoving', (0, 0, 0), u'Орудийная')], 'ru')
        separated = buildOverlayData([
            MarkerData('gunStatic', (0, 0, 0), u'Исходная'),
            MarkerData('gunMoving', (1, 0, 0), u'Орудийная')], 'ru')

        self.assertIn(u'две точки', merged[0]['tooltipBody'])
        self.assertEqual(merged[0]['tooltipBody'].count(u'\n\n'), 3)
        self.assertNotIn(u'две точки', separated[1]['tooltipBody'])


if __name__ == '__main__':
    unittest.main()
