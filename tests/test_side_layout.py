import os
import json
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
    def test_continuous_row_motion_follows_its_neighbour_immediately(self):
        solver = SideLayoutSolver()
        for shortY in (380, 381, 383, 382, 380):
            result = solver.solve(1400, 900, box(300, 250, 900, 550),
                                  box(500, 220, 700, 420),
                                  [item('short', 890, shortY), item('long', 760, 386)])
            placements = dict((p['id'], p) for p in result['placements'])
            self.assertAlmostEqual(placements['long']['rect'][1],
                                   placements['short']['rect'][1] + 30.0)

    def test_row_holds_through_small_y_changes_but_releases_a_collision(self):
        solver = SideLayoutSolver()
        def frame(y):
            result = solver.solve(1400, 900, box(300, 250, 900, 550),
                                  box(500, 220, 700, 420),
                                  [item('short', 890, 380), item('long', 760, y)])
            return dict((p['id'], p) for p in result['placements'])
        for y in (382, 381, 379, 382, 378):
            placements = frame(y)
            self.assertGreater(placements['long']['rect'][1],
                               placements['short']['rect'][1])
        placements = frame(370)
        self.assertLess(placements['long']['rect'][1], placements['short']['rect'][1])
        self.assertEqual(rectangleIntersectionArea(placements['long']['rect'],
                                                   placements['short']['rect']), 0)

    def test_side_does_not_chatter_near_equal_projection_lengths(self):
        solver = SideLayoutSolver()
        def frame(x):
            return solver.solve(1400, 900, box(300, 250, 900, 550),
                                box(500, 220, 700, 420), [item('a', x, 380)])
        self.assertEqual(frame(599)['placements'][0]['lane'], 'left')
        for x in (601, 598, 602, 599, 601):
            placement = frame(x)['placements'][0]
            self.assertEqual(placement['lane'], 'left')
            self.assertEqual(placement['leader'][0], [x, 380])
        self.assertEqual(frame(650)['placements'][0]['lane'], 'right')
        solver.reset()
        self.assertEqual(frame(599)['placements'][0]['lane'], 'left')

    def test_short_front_projection_is_not_displaced_by_long_gun_callouts(self):
        path = os.path.join(os.path.dirname(__file__), 'fixtures',
                            'callouts_side_view.json')
        with open(path) as stream:
            args = json.load(stream)
        result = SideLayoutSolver().solve(*args)
        placements = dict((p['id'], p) for p in result['placements'])
        front = placements['front']
        self.assertTrue(all(abs(p[1] - front['leader'][0][1]) < 0.01
                            for p in front['leader']))
        for i, a in enumerate(result['placements']):
            for b in result['placements'][i + 1:]:
                self.assertEqual(rectangleIntersectionArea(a['rect'], b['rect']), 0)
                self.assertFalse(_polylinesIntersect(a['leader'], b['leader']),
                                 (a['id'], b['id']))

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

    def test_crowded_side_keeps_screen_order_when_a_middle_row_is_full(self):
        items = [item('a', 796, 372), item('b', 735, 402),
                 item('c', 711, 380), item('short', 877, 354),
                 item('d', 813, 387)]
        placements = dict((p['id'], p) for p in self.solve(items)['placements'])
        for lane in ('left', 'right'):
            ordered = [placements[p['id']]
                       for p in sorted(items, key=lambda p: p['y'])
                       if placements[p['id']]['lane'] == lane]
            for above, below in zip(ordered, ordered[1:]):
                self.assertLessEqual(above['rect'][1] + above['rect'][3] + 6,
                                     below['rect'][1])
        self.assertTrue(all(p[1] == 354 for p in placements['short']['leader']))

    def test_depth_does_not_override_screen_order(self):
        items = [dict(item('short', 890, 380), depth=10.0),
                 dict(item('far-below', 720, 384), depth=15.0),
                 dict(item('near-above', 760, 376), depth=5.0)]
        placements = dict((p['id'], p) for p in self.solve(items)['placements'])
        self.assertLess(placements['near-above']['rect'][1], placements['short']['rect'][1])
        self.assertGreater(placements['far-below']['rect'][1], placements['short']['rect'][1])

    def test_non_conflicting_rows_stay_horizontal(self):
        items = [item('upper', 720, 290), item('short', 890, 380),
                 item('lower', 760, 500)]
        for placement in self.solve(items)['placements']:
            self.assertTrue(all(p[1] == placement['leader'][0][1]
                                for p in placement['leader']))


if __name__ == '__main__':
    unittest.main()
