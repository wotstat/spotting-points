# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class MarkerLogicTests(unittest.TestCase):
    def test_overlay_is_active_only_with_hangar_and_no_covering_view(self):
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

        markers = buildMarkerData(mask, spots)

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

        markers = buildMarkerData(mask, spots)

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

        payload = buildOverlayData(markers)

        self.assertEqual(payload, [
            {'id': 'front', 'label': u'Передняя', 'showLabel': True},
            {'id': 'rear', 'label': u'Задняя', 'showLabel': True},
            {'id': 'left', 'label': u'Левая', 'showLabel': True},
        ])


if __name__ == '__main__':
    unittest.main()
