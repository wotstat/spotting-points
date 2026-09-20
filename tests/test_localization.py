# -*- coding: utf-8 -*-
import os
import sys
import types
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        from wotstat_spotting_points import localization
        self.localization = localization

    def test_all_target_languages_have_complete_labels(self):
        expected = set((
            'be', 'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr',
            'hr', 'hu', 'it', 'lt', 'lv', 'nl', 'no', 'pl', 'pt', 'ro',
            'ru', 'sr', 'sv', 'tr', 'uk',
        ))
        self.assertEqual(set(self.localization.SUPPORTED_LANGUAGES), expected)
        self.assertEqual(set(self.localization._TRANSLATIONS), expected)
        for language in expected:
            self.assertEqual(
                len(self.localization._TRANSLATIONS[language]),
                len(self.localization._KEYS))
            modList = self.localization.getModListLabels(language)
            settings = self.localization.getSettingsLabels(language)
            markers = self.localization.getMarkerLabels(language)
            self.assertEqual(set(modList), set(('name', 'description')))
            self.assertEqual(len(settings), 11)
            self.assertEqual(len(settings['calloutModes']), 3)
            self.assertEqual(len(markers), 7)
            self.assertTrue(all(modList.values()))
            self.assertTrue(all(settings.values()))
            self.assertTrue(all(markers.values()))

    def test_russian_mod_list_name_is_short(self):
        labels = self.localization.getModListLabels('ru')
        self.assertEqual(labels['name'], u'Габаритные точки')

    def test_region_suffix_and_unknown_language_fallback(self):
        self.assertEqual(self.localization.normalizeLanguage('pt-BR'), 'pt')
        self.assertEqual(self.localization.normalizeLanguage('be_BY'), 'be')
        self.assertEqual(self.localization.normalizeLanguage('xx'), 'en')

    def test_client_language_is_selected_automatically(self):
        previous = sys.modules.get('helpers')
        helpers = types.ModuleType('helpers')
        helpers.getClientLanguage = lambda: 'de'
        sys.modules['helpers'] = helpers
        try:
            labels = self.localization.getModListLabels()
        finally:
            if previous is None:
                del sys.modules['helpers']
            else:
                sys.modules['helpers'] = previous
        self.assertEqual(labels['name'], u'Umrisspunkte')


if __name__ == '__main__':
    unittest.main()
