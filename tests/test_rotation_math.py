import math
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class RotationMathTests(unittest.TestCase):
    def test_rotating_hit_preserves_static_part_and_distance(self):
        from wotstat_spotting_points.rotation_math import findRotatingPartHit

        self.assertEqual(findRotatingPartHit(
            [(6, 8.0), (5, 9.0), (3, 10.5)], 3, 2, 3),
            (3, 10.5))
        self.assertEqual(findRotatingPartHit(
            [(6, 8.0), (2, 11.25)], 3, 2, 3),
            (2, 11.25))

    def test_rotating_hit_skips_styled_parts_inside_static_collision_range(self):
        from wotstat_spotting_points.rotation_math import findRotatingPartHit

        self.assertEqual(findRotatingPartHit(
            [(6, 9.575), (2, 10.353), (2, 11.346)], 7, 2, 3),
            (2, 10.353))
        self.assertEqual(findRotatingPartHit(
            [(6, 8.387), (5, 9.688), (3, 10.958)], 7, 2, 3),
            (3, 10.958))

    def test_turret_and_gun_drags_use_every_available_axis(self):
        from wotstat_spotting_points.rotation_math import (
            canStartPartDrag, getDragAxes)

        self.assertEqual(getDragAxes(2, 2, 3, True, True), (True, True))
        self.assertEqual(getDragAxes(3, 2, 3, True, True), (True, True))
        self.assertEqual(getDragAxes(3, 2, 3, False, True), (False, True))
        self.assertTrue(canStartPartDrag(2, 2, 3, True, False))
        self.assertTrue(canStartPartDrag(2, 2, 3, False, True))
        self.assertTrue(canStartPartDrag(3, 2, 3, False, True))
        self.assertTrue(canStartPartDrag(3, 2, 3, True, False))

    def test_mouse_right_always_turns_counterclockwise_at_double_sensitivity(self):
        from wotstat_spotting_points.rotation_math import nextAngles

        yaw, pitch = nextAngles(
            1.0, 0.0, 100.0, 50.0, None, (-0.2, 0.3))

        self.assertAlmostEqual(yaw, 0.7)
        self.assertAlmostEqual(pitch, 0.15)

    def test_rotating_part_hit_ignores_procedural_attachments(self):
        from wotstat_spotting_points.rotation_math import isRotatingPartHit

        self.assertTrue(isRotatingPartHit([5, 4, 3], 3, 2, 3))
        self.assertTrue(isRotatingPartHit([6, 2], 3, 2, 3))

    def test_rotating_part_hit_stops_at_first_static_part(self):
        from wotstat_spotting_points.rotation_math import isRotatingPartHit

        self.assertFalse(isRotatingPartHit([6, 0, 3], 3, 2, 3))
        self.assertFalse(isRotatingPartHit([6, 5], 3, 2, 3))

    def test_full_circle_yaw_stays_normalized(self):
        from wotstat_spotting_points.rotation_math import nextAngles
        yaw, pitch = nextAngles(math.pi - 0.01, 0.0, -100.0, 0.0,
                                None, (-0.2, 0.3))

        self.assertTrue(0.0 <= yaw < 2.0 * math.pi)
        self.assertAlmostEqual(yaw, math.pi + 0.29)
        self.assertEqual(pitch, 0.0)

    def test_limited_yaw_and_pitch_are_clamped(self):
        from wotstat_spotting_points.rotation_math import nextAngles
        yaw, pitch = nextAngles(0.0, 0.0, -1000.0, 1000.0,
                                (-0.4, 0.5), (-0.1, 0.2))

        self.assertEqual((yaw, pitch), (0.5, 0.2))

    def test_zero_delta_preserves_angles(self):
        from wotstat_spotting_points.rotation_math import nextAngles

        self.assertEqual(nextAngles(0.2, -0.1, 0.0, 0.0,
                                    (-0.5, 0.5), (-0.2, 0.3)),
                         (0.2, -0.1))

    def test_static_axes_ignore_drag_and_limit_recalculation(self):
        from wotstat_spotting_points.rotation_math import nextAngles

        self.assertEqual(nextAngles(0.2, -0.1, 1000.0, 1000.0,
                                    (-0.05, 0.05), (-0.05, 0.05),
                                    changeYaw=False, changePitch=False),
                         (0.2, -0.1))


if __name__ == '__main__':
    unittest.main()
