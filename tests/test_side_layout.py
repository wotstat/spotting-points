import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))

from wotstat_spotting_points.layout_solver import (
    rectangleIntersectionArea, _polylinesIntersect)
from wotstat_spotting_points.side_layout import SideLayoutSolver


def box(left, top, right, bottom):
    return [(left, top), (right, top), (right, bottom), (left, bottom)]


def item(pointId, x, y):
    return dict(id=pointId, x=x, y=y, width=140.0, height=24.0, part='hull')


class SideLayoutTests(unittest.TestCase):
    def solve(self, items):
        return SideLayoutSolver().solve(
            1400, 900, box(300, 250, 900, 550), box(500, 220, 700, 420),
            items)

    def test_even_roof_point_uses_horizontal_side_projection(self):
        placement = self.solve([item('top', 600, 255)])['placements'][0]
        self.assertIn(placement['lane'], ('left', 'right'))
        self.assertTrue(all(p[1] == 255 for p in placement['leader']))

    def test_shortest_line_stays_straight_and_longer_labels_keep_order(self):
        result = self.solve([item('long-above', 720, 378),
                             item('short', 890, 380),
                             item('long-below', 760, 382)])
        placements = dict((p['id'], p) for p in result['placements'])
        short = placements['short']
        self.assertTrue(all(p[1] == 380 for p in short['leader']))
        above, below = placements['long-above'], placements['long-below']
        self.assertLess(above['rect'][1], short['rect'][1])
        self.assertGreater(below['rect'][1], short['rect'][1])
        for i, a in enumerate(result['placements']):
            for b in result['placements'][i + 1:]:
                self.assertEqual(rectangleIntersectionArea(a['rect'], b['rect']), 0)
                self.assertFalse(_polylinesIntersect(a['leader'], b['leader']))

    def test_input_order_does_not_change_the_layout(self):
        items = [item('a', 880, 375), item('b', 810, 381),
                 item('c', 750, 384), item('d', 320, 380)]
        self.assertEqual(self.solve(items), self.solve(list(reversed(items))))

    def test_anchor_outside_viewport_still_has_a_callout(self):
        placement = self.solve([item('offscreen', 600, -1000)])['placements'][0]
        self.assertIn(placement['lane'], ('left', 'right'))
        self.assertEqual(placement['leader'][0], [600, -1000])
        self.assertGreaterEqual(placement['rect'][1], 0)


if __name__ == '__main__':
    unittest.main()
