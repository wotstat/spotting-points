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
            'showUiPoints': False,
            'showGuides': False,
            'allowTurretRotation': False,
            'layoutDebug': False,
            'calloutMode': 2,
        })
        self.assertFalse(options.hasVisuals())

    def test_callout_modes_preserve_numeric_selection(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()
        for mode in (0, 1, 2):
            self.assertTrue(options.setValue('calloutMode', mode))
            self.assertEqual(options.asDict()['calloutMode'], mode)
            self.assertFalse(options.hasVisuals())
        self.assertFalse(options.setValue('calloutMode', 3))
        self.assertEqual(options.calloutMode, 2)

    def test_ui_points_are_an_independent_visual(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()

        self.assertTrue(options.setValue('showUiPoints', True))
        self.assertTrue(options.showUiPoints)
        self.assertFalse(options.showMaskPoints)
        self.assertFalse(options.showSpotPoints)
        self.assertTrue(options.hasVisuals())

    def test_ui_only_mode_uses_bounded_update_interval(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()
        options.showUiPoints = True

        self.assertAlmostEqual(options.drawInterval(False), 1.0 / 30.0)
        self.assertEqual(options.drawInterval(True), 0.0)
        options.showMaskPoints = True
        self.assertEqual(options.drawInterval(False), 0.0)

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

    def test_layout_debug_does_not_start_visuals_by_itself(self):
        from wotstat_spotting_points.options import DisplayOptions
        options = DisplayOptions()

        self.assertTrue(options.setValue('layoutDebug', True))
        self.assertTrue(options.layoutDebug)
        self.assertFalse(options.hasVisuals())


if __name__ == '__main__':
    unittest.main()
