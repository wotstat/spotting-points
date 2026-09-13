import math
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class RotationMathTests(unittest.TestCase):
    def test_full_circle_yaw_is_normalized(self):
        from wotstat_spotting_points.rotation_math import nextAngles
        yaw, pitch = nextAngles(math.pi - 0.01, 0.0, -100.0, 0.0,
                                None, (-0.2, 0.3))

        self.assertTrue(-math.pi <= yaw < math.pi)
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
