import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))

from wotstat_spotting_points.callout_transition import CalloutTransitions, TRANSITION_SECONDS


def layout(x, y=288.0, lane='left', anchor=(400.0, 300.0)):
    edge = x + 140.0 if lane == 'left' else x
    return dict(revision=1, placements=[dict(
        id='a', lane=lane, rect=[x, y, 140.0, 24.0],
        leader=[list(anchor), [anchor[0], y + 12.0], [edge, y + 12.0]])])


class CalloutTransitionTests(unittest.TestCase):
    def test_initial_placement_and_small_motion_are_immediate(self):
        renderer = CalloutTransitions()
        self.assertEqual(renderer.apply(layout(100), 0)['placements'][0]['rect'][0], 100)
        self.assertEqual(renderer.apply(layout(102, 290), 0.01)['placements'][0]['rect'][:2],
                         [102, 290])
        self.assertNotIn('placements', renderer.apply({'revision': 1}, 0.02))

    def test_side_jump_animates_straight_and_finishes_with_cached_input(self):
        renderer = CalloutTransitions()
        renderer.apply(layout(100), 0)
        target = layout(600, 348, 'right')
        start = renderer.apply(target, 1)['placements'][0]
        self.assertEqual(start['rect'][:2], [100, 288])
        middle = renderer.apply({'revision': 1}, 1.09)['placements'][0]
        ratioX = (middle['rect'][0] - 100) / 500.0
        ratioY = (middle['rect'][1] - 288) / 60.0
        self.assertGreater(ratioX, 0)
        self.assertLess(ratioX, 1)
        self.assertAlmostEqual(ratioX, ratioY)
        end = renderer.apply({'revision': 1}, 1 + TRANSITION_SECONDS + 0.01)['placements'][0]
        self.assertEqual(end, target['placements'][0])
        self.assertEqual(target, layout(600, 348, 'right'))
        self.assertNotIn('placements', renderer.apply({'revision': 1}, 1.3))

    def test_continuous_camera_motion_does_not_restart_active_tween(self):
        renderer = CalloutTransitions()
        renderer.apply(layout(100), 0)
        renderer.apply(layout(600, lane='right'), 1)
        moved = layout(700, 328, 'right', (500, 340))
        middle = renderer.apply(moved, 1.09)['placements'][0]
        self.assertEqual(middle['leader'][0], [500, 340])
        self.assertGreater(middle['rect'][0], 200)
        self.assertLess(middle['rect'][0], 700)
        self.assertEqual(renderer.apply({'revision': 1}, 1 + TRANSITION_SECONDS + 0.01)['placements'][0],
                         moved['placements'][0])

    def test_new_jump_starts_from_current_animated_position(self):
        renderer = CalloutTransitions()
        renderer.apply(layout(100), 0)
        renderer.apply(layout(600, lane='right'), 1)
        middle = renderer.apply({'revision': 1}, 1.09)['placements'][0]
        retarget = renderer.apply(layout(80), 1.09)['placements'][0]
        self.assertEqual(retarget['rect'], middle['rect'])
        self.assertEqual(renderer.apply({'revision': 1}, 1.09 + TRANSITION_SECONDS + 0.01)['placements'][0]['rect'][0], 80)

    def test_row_jump_animates_and_reset_clears_the_transition(self):
        renderer = CalloutTransitions()
        renderer.apply(layout(100), 0)
        start = renderer.apply(layout(100, 348), 1)['placements'][0]
        self.assertEqual(start['rect'][1], 288)
        renderer.reset()
        self.assertEqual(renderer.apply(layout(100, 348), 1.01)['placements'][0]['rect'][1], 348)


if __name__ == '__main__':
    unittest.main()
