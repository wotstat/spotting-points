import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class DisplayOptionsTests(unittest.TestCase):
    def test_defaults_disable_every_feature(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()

        self.assertEqual(options.asDict(), {
            'showMaskPoints': False,
            'showSpotPoints': False,
            'showGuides': False,
            'allowTurretRotation': False,
        })
        self.assertFalse(options.hasVisuals())

    def test_updates_visuals_and_rotation_independently(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()

        self.assertTrue(options.setValue('showSpotPoints', True))
        self.assertTrue(options.showSpotPoints)
        self.assertTrue(options.hasVisuals())
        self.assertFalse(options.allowTurretRotation)
        self.assertTrue(options.setValue('allowTurretRotation', True))
        self.assertTrue(options.allowTurretRotation)

    def test_rejects_unknown_option_without_adding_it(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()

        self.assertFalse(options.setValue('unknown', True))
        self.assertFalse(hasattr(options, 'unknown'))


if __name__ == '__main__':
    unittest.main()
