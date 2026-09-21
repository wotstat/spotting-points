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
                set(self.localization._TRANSLATIONS[language]),
                set(self.localization._KEYS))
            modList = self.localization.getModListLabels(language)
            settings = self.localization.getSettingsLabels(language)
            markers = self.localization.getMarkerLabels(language)
            tooltips = self.localization.getMarkerTooltips(language)
            self.assertEqual(set(modList), set(('name', 'description')))
            self.assertEqual(len(settings), 12)
            self.assertEqual(len(settings['calloutModes']), 3)
            self.assertEqual(len(markers), 7)
            self.assertTrue(all(modList.values()))
            self.assertTrue(all(settings.values()))
            self.assertTrue(all(markers.values()))
            self.assertEqual(set(tooltips), set(markers) | {'combinedGun'})
            self.assertTrue(all(tooltip['title'] and tooltip['body']
                                for tooltip in tooltips.values()))

    def test_russian_combined_gun_tooltip_preserves_paragraphs(self):
        tooltip = self.localization.getMarkerTooltips('ru')['combinedGun']
        self.assertEqual(tooltip['title'],
                         u'Исходная орудийная габаритная и орудийная '
                         u'обзорно-габаритная')
        self.assertEqual(len(tooltip['body'].split(u'\n\n')), 4)

    def test_russian_mod_list_name_is_short(self):
        labels = self.localization.getModListLabels('ru')
        self.assertEqual(labels['name'], u'Габаритные точки')

    def test_tooltip_option_has_localized_label(self):
        self.assertEqual(self.localization.getSettingsLabels('ru')['showTooltips'],
                         u'Отображать подсказки')
        self.assertEqual(self.localization.getSettingsLabels('en')['showTooltips'],
                         u'Show tooltips')

    def test_point_terminology_matches_game_usage(self):
        expected = {
            'be': (u'Габарытныя кропкі', u'Аглядныя кропкі'),
            'bg': (u'Контролни точки на видимостта', u'Обзорни точки'),
            'cs': (u'Body viditelnosti', u'Porty dohledu'),
            'da': (u'Synlighedskontrolpunkter', u'Observationspunkter'),
            'de': (u'Sichtbarkeitspunkte', u'Sichtfenster'),
            'el': (u'Σημεία ελέγχου ορατότητας', u'Σημεία παρατήρησης'),
            'en': (u'Visibility checkpoints', u'View range ports'),
            'es': (u'Puntos de control de visibilidad',
                   u'Puertos de alcance de visión'),
            'fi': (u'Näkyvyyden tarkistuspisteet', u'Tähystyspisteet'),
            'fr': (u'Points de visibilité', u'Ports de portée de vue'),
            'hr': (u'Točke vidljivosti', u'Osmatračke točke'),
            'hu': (u'Láthatósági ellenőrzőpontok', u'Látótávolsági portok'),
            'it': (u'Punti di controllo di visibilità',
                   u'Feritoie del raggio visivo'),
            'lt': (u'Matomumo kontrolės taškai', u'Stebėjimo taškai'),
            'lv': (u'Redzamības kontrolpunkti', u'Novērošanas punkti'),
            'nl': (u'Zichtbaarheidscontrolepunten', u'Waarnemingspunten'),
            'no': (u'Synlighetskontrollpunkter', u'Observasjonspunkter'),
            'pl': (u'Punkty kontrolne widoczności',
                   u'Porty zasięgu widzenia'),
            'pt': (u'Pontos de detecção', u'Portas de visão'),
            'ro': (u'Puncte de control al vizibilității',
                   u'Puncte de vizualizare'),
            'ru': (u'Габаритные точки', u'Обзорные точки'),
            'sr': (u'Tačke vidljivosti', u'Osmatračke tačke'),
            'sv': (u'Synlighetskontrollpunkter', u'Observationspunkter'),
            'tr': (u'Görüş kontrol noktaları', u'Görüş menzili yuvaları'),
            'uk': (u'Габаритні точки', u'Оглядові точки'),
        }
        for language, terms in expected.items():
            labels = self.localization.getSettingsLabels(language)
            self.assertEqual(labels['showMaskPoints'], terms[0])
            self.assertEqual(labels['showSpotPoints'], terms[1])

    def test_english_combined_markers_name_both_point_types(self):
        markers = self.localization.getMarkerLabels('en')
        self.assertEqual(
            markers['top'],
            u'Upper visibility checkpoint / view range port')
        self.assertEqual(
            markers['gunMoving'],
            u'Gun visibility checkpoint / view range port')

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
        self.assertEqual(labels['name'], u'Sichtbarkeitspunkte')


if __name__ == '__main__':
    unittest.main()
