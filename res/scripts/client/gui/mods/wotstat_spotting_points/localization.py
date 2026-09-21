# -*- coding: utf-8 -*-

DEFAULT_LANGUAGE = 'en'
SUPPORTED_LANGUAGES = (
    'be', 'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'hr',
    'hu', 'it', 'lt', 'lv', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sr',
    'sv', 'tr', 'uk',
)

_KEYS = (
    'modName', 'modDescription', 'title',
    'showMaskPoints', 'showSpotPoints', 'showUiPoints', 'showGuides',
    'group3d', 'groupUi', 'callouts',
    'calloutOff', 'calloutA', 'calloutB',
    'allowTurretRotation', 'layoutDebug',
    'rear', 'front', 'left', 'right', 'gunStatic', 'top', 'gunMoving',
)

# The target locale list comes from the wot-eu and mt-ru client snapshots.
# Point names follow official game terminology where it is published.  For
# locales without an attested game term, the closest semantic translation is
# used.  A compact ordered table keeps every locale easy to audit.
_TRANSLATIONS = {
    'be': u'Габарытныя кропкі|Налады габарытных і аглядных кропак|Габарытныя і аглядныя кропкі|Габарытныя кропкі|Аглядныя кропкі|Паказваць маркеры|Накіравальныя|3D|UI|Подпісы|Не паказваць|Варыянт А|Варыянт Б|Дазволіць варочаць вежу мышшу|Адладачная адмалёўка зон размяшчэння|Задняя габарытная|Пярэдняя габарытная|Левая бартавая габарытная|Правая бартавая габарытная|Пачатковая гарматная габарытная|Верхняя аглядна-габарытная|Гарматная аглядна-габарытная'.split(u'|'),
    'bg': u'Контролни точки на видимостта|Настройки на контролните точки на видимостта и обзорните точки|Контролни точки на видимостта и обзорни точки|Контролни точки на видимостта|Обзорни точки|Показване на маркерите|Водачи|3D|UI|Етикети|Без показване|Вариант A|Вариант B|Разрешаване на въртенето на кулата с мишката|Отладъчно изчертаване на зоните за разполагане|Задна контролна точка на видимостта|Предна контролна точка на видимостта|Лява странична контролна точка на видимостта|Дясна странична контролна точка на видимостта|Изходна контролна точка на видимостта при оръдието|Горна контролна точка на видимостта / обзорна точка|Контролна точка на видимостта при оръдието / обзорна точка'.split(u'|'),
    'cs': u'Body viditelnosti|Nastavení bodů viditelnosti a portů dohledu|Body viditelnosti a porty dohledu|Body viditelnosti|Porty dohledu|Zobrazit značky|Vodicí čáry|3D|UI|Popisky|Nezobrazovat|Varianta A|Varianta B|Povolit otáčení věže myší|Ladicí vykreslení zón umístění|Zadní bod viditelnosti|Přední bod viditelnosti|Levý boční bod viditelnosti|Pravý boční bod viditelnosti|Výchozí bod viditelnosti děla|Horní bod viditelnosti / port dohledu|Bod viditelnosti děla / port dohledu'.split(u'|'),
    'da': u'Synlighedskontrolpunkter|Indstillinger for synlighedskontrol- og observationspunkter|Synlighedskontrol- og observationspunkter|Synlighedskontrolpunkter|Observationspunkter|Vis markører|Hjælpelinjer|3D|UI|Etiketter|Vis ikke|Variant A|Variant B|Tillad tårnrotation med musen|Fejlfindingsvisning af placeringszoner|Bageste synlighedskontrolpunkt|Forreste synlighedskontrolpunkt|Venstre synlighedskontrolpunkt|Højre synlighedskontrolpunkt|Fast synlighedskontrolpunkt ved kanonen|Øverste synlighedskontrolpunkt / observationspunkt|Kanonens synlighedskontrolpunkt / observationspunkt'.split(u'|'),
    'de': u'Sichtbarkeitspunkte|Einstellungen für Sichtbarkeitspunkte und Sichtfenster|Sichtbarkeitspunkte und Sichtfenster|Sichtbarkeitspunkte|Sichtfenster|Markierungen anzeigen|Hilfslinien|3D|UI|Beschriftungen|Nicht anzeigen|Variante A|Variante B|Turmdrehung mit der Maus erlauben|Debuganzeige der Platzierungszonen|Hinterer Sichtbarkeitspunkt|Vorderer Sichtbarkeitspunkt|Linker seitlicher Sichtbarkeitspunkt|Rechter seitlicher Sichtbarkeitspunkt|Fester Sichtbarkeitspunkt am Geschütz|Oberer Sichtbarkeitspunkt / Sichtfenster|Sichtbarkeitspunkt am Geschütz / Sichtfenster'.split(u'|'),
    'el': u'Σημεία ελέγχου ορατότητας|Ρυθμίσεις σημείων ελέγχου ορατότητας και παρατήρησης|Σημεία ελέγχου ορατότητας και παρατήρησης|Σημεία ελέγχου ορατότητας|Σημεία παρατήρησης|Εμφάνιση δεικτών|Γραμμές οδήγησης|3D|UI|Ετικέτες|Να μην εμφανίζονται|Παραλλαγή A|Παραλλαγή B|Να επιτρέπεται η περιστροφή πύργου με το ποντίκι|Εμφάνιση αποσφαλμάτωσης ζωνών τοποθέτησης|Πίσω σημείο ελέγχου ορατότητας|Μπροστινό σημείο ελέγχου ορατότητας|Αριστερό πλευρικό σημείο ελέγχου ορατότητας|Δεξί πλευρικό σημείο ελέγχου ορατότητας|Σταθερό σημείο ελέγχου ορατότητας πυροβόλου|Επάνω σημείο ελέγχου ορατότητας / σημείο παρατήρησης|Σημείο ελέγχου ορατότητας πυροβόλου / σημείο παρατήρησης'.split(u'|'),
    'en': u'Visibility checkpoints|Configure visibility checkpoints and view range ports|Visibility checkpoints and view range ports|Visibility checkpoints|View range ports|Show markers|Guides|3D|UI|Labels|Do not show|Variant A|Variant B|Allow mouse turret rotation|Debug drawing of placement zones|Rear visibility checkpoint|Front visibility checkpoint|Left-side visibility checkpoint|Right-side visibility checkpoint|Initial gun visibility checkpoint|Upper visibility checkpoint / view range port|Gun visibility checkpoint / view range port'.split(u'|'),
    'es': u'Puntos de control de visibilidad|Ajustes de los puntos de control de visibilidad y puertos de alcance de visión|Puntos de control de visibilidad y puertos de alcance de visión|Puntos de control de visibilidad|Puertos de alcance de visión|Mostrar marcadores|Guías|3D|IU|Etiquetas|No mostrar|Variante A|Variante B|Permitir girar la torreta con el ratón|Dibujo de depuración de zonas de colocación|Punto de control de visibilidad trasero|Punto de control de visibilidad delantero|Punto de control de visibilidad lateral izquierdo|Punto de control de visibilidad lateral derecho|Punto de control de visibilidad inicial del cañón|Punto de control de visibilidad superior / puerto de alcance de visión|Punto de control de visibilidad del cañón / puerto de alcance de visión'.split(u'|'),
    'fi': u'Näkyvyyden tarkistuspisteet|Näkyvyyden tarkistus- ja tähystyspisteiden asetukset|Näkyvyyden tarkistus- ja tähystyspisteet|Näkyvyyden tarkistuspisteet|Tähystyspisteet|Näytä merkit|Apulinjat|3D|UI|Nimilaput|Älä näytä|Vaihtoehto A|Vaihtoehto B|Salli tornin kääntäminen hiirellä|Sijoitusalueiden virheenkorjauspiirto|Takimmainen näkyvyyden tarkistuspiste|Etummainen näkyvyyden tarkistuspiste|Vasen näkyvyyden tarkistuspiste|Oikea näkyvyyden tarkistuspiste|Tykin kiinteä näkyvyyden tarkistuspiste|Ylempi näkyvyyden tarkistuspiste / tähystyspiste|Tykin näkyvyyden tarkistuspiste / tähystyspiste'.split(u'|'),
    'fr': u'Points de visibilité|Réglages des points de visibilité et des ports de portée de vue|Points de visibilité et ports de portée de vue|Points de visibilité|Ports de portée de vue|Afficher les marqueurs|Repères|3D|UI|Étiquettes|Ne pas afficher|Variante A|Variante B|Autoriser la rotation de la tourelle à la souris|Affichage de débogage des zones de placement|Point de visibilité arrière|Point de visibilité avant|Point de visibilité latéral gauche|Point de visibilité latéral droit|Point de visibilité initial du canon|Point de visibilité supérieur / port de portée de vue|Point de visibilité du canon / port de portée de vue'.split(u'|'),
    'hr': u'Točke vidljivosti|Postavke točaka vidljivosti i osmatračkih točaka|Točke vidljivosti i osmatračke točke|Točke vidljivosti|Osmatračke točke|Prikaži oznake|Vodilice|3D|UI|Natpisi|Ne prikazuj|Varijanta A|Varijanta B|Dopusti okretanje kupole mišem|Prikaz zona postavljanja za otklanjanje pogrešaka|Stražnja točka vidljivosti|Prednja točka vidljivosti|Lijeva bočna točka vidljivosti|Desna bočna točka vidljivosti|Početna točka vidljivosti topa|Gornja točka vidljivosti / osmatračka točka|Točka vidljivosti topa / osmatračka točka'.split(u'|'),
    'hu': u'Láthatósági ellenőrzőpontok|A láthatósági ellenőrzőpontok és látótávolsági portok beállításai|Láthatósági ellenőrzőpontok és látótávolsági portok|Láthatósági ellenőrzőpontok|Látótávolsági portok|Jelölők megjelenítése|Segédvonalak|3D|UI|Címkék|Ne jelenjen meg|A változat|B változat|Torony forgatása egérrel|Elhelyezési zónák hibakeresési rajza|Hátsó láthatósági ellenőrzőpont|Első láthatósági ellenőrzőpont|Bal oldali láthatósági ellenőrzőpont|Jobb oldali láthatósági ellenőrzőpont|Löveg kezdeti láthatósági ellenőrzőpontja|Felső láthatósági ellenőrzőpont / látótávolsági port|Löveg láthatósági ellenőrzőpontja / látótávolsági portja'.split(u'|'),
    'it': u'Punti di controllo di visibilità|Impostazioni dei punti di controllo di visibilità e delle feritoie del raggio visivo|Punti di controllo di visibilità e feritoie del raggio visivo|Punti di controllo di visibilità|Feritoie del raggio visivo|Mostra indicatori|Linee guida|3D|UI|Etichette|Non mostrare|Variante A|Variante B|Consenti la rotazione della torretta con il mouse|Disegno di debug delle zone di posizionamento|Punto di controllo di visibilità posteriore|Punto di controllo di visibilità anteriore|Punto di controllo di visibilità laterale sinistro|Punto di controllo di visibilità laterale destro|Punto di controllo di visibilità iniziale del cannone|Punto di controllo di visibilità superiore / feritoia del raggio visivo|Punto di controllo di visibilità del cannone / feritoia del raggio visivo'.split(u'|'),
    'lt': u'Matomumo kontrolės taškai|Matomumo kontrolės ir stebėjimo taškų nustatymai|Matomumo kontrolės ir stebėjimo taškai|Matomumo kontrolės taškai|Stebėjimo taškai|Rodyti žymeklius|Kreipiamosios|3D|UI|Etiketės|Nerodyti|A variantas|B variantas|Leisti sukti bokštelį pele|Išdėstymo zonų derinimo vaizdas|Galinis matomumo kontrolės taškas|Priekinis matomumo kontrolės taškas|Kairysis šoninis matomumo kontrolės taškas|Dešinysis šoninis matomumo kontrolės taškas|Pradinis pabūklo matomumo kontrolės taškas|Viršutinis matomumo kontrolės taškas / stebėjimo taškas|Pabūklo matomumo kontrolės taškas / stebėjimo taškas'.split(u'|'),
    'lv': u'Redzamības kontrolpunkti|Redzamības kontrolpunktu un novērošanas punktu iestatījumi|Redzamības kontrolpunkti un novērošanas punkti|Redzamības kontrolpunkti|Novērošanas punkti|Rādīt marķierus|Palīglīnijas|3D|UI|Iezīmes|Nerādīt|A variants|B variants|Atļaut torņa pagriešanu ar peli|Izvietojuma zonu atkļūdošanas zīmējums|Aizmugurējais redzamības kontrolpunkts|Priekšējais redzamības kontrolpunkts|Kreisais sānu redzamības kontrolpunkts|Labais sānu redzamības kontrolpunkts|Sākotnējais lielgabala redzamības kontrolpunkts|Augšējais redzamības kontrolpunkts / novērošanas punkts|Lielgabala redzamības kontrolpunkts / novērošanas punkts'.split(u'|'),
    'nl': u'Zichtbaarheidscontrolepunten|Instellingen voor zichtbaarheidscontrole- en waarnemingspunten|Zichtbaarheidscontrole- en waarnemingspunten|Zichtbaarheidscontrolepunten|Waarnemingspunten|Markeringen tonen|Hulplijnen|3D|UI|Labels|Niet tonen|Variant A|Variant B|Torenrotatie met de muis toestaan|Debugweergave van plaatsingszones|Achterste zichtbaarheidscontrolepunt|Voorste zichtbaarheidscontrolepunt|Linker zichtbaarheidscontrolepunt|Rechter zichtbaarheidscontrolepunt|Vast zichtbaarheidscontrolepunt van het kanon|Bovenste zichtbaarheidscontrolepunt / waarnemingspunt|Zichtbaarheidscontrolepunt van het kanon / waarnemingspunt'.split(u'|'),
    'no': u'Synlighetskontrollpunkter|Innstillinger for synlighetskontroll- og observasjonspunkter|Synlighetskontroll- og observasjonspunkter|Synlighetskontrollpunkter|Observasjonspunkter|Vis markører|Hjelpelinjer|3D|UI|Etiketter|Ikke vis|Variant A|Variant B|Tillat tårnrotasjon med musen|Feilsøkingsvisning av plasseringssoner|Bakre synlighetskontrollpunkt|Fremre synlighetskontrollpunkt|Venstre synlighetskontrollpunkt|Høyre synlighetskontrollpunkt|Fast synlighetskontrollpunkt ved kanonen|Øvre synlighetskontrollpunkt / observasjonspunkt|Kanonens synlighetskontrollpunkt / observasjonspunkt'.split(u'|'),
    'pl': u'Punkty kontrolne widoczności|Ustawienia punktów kontrolnych widoczności i portów zasięgu widzenia|Punkty kontrolne widoczności i porty zasięgu widzenia|Punkty kontrolne widoczności|Porty zasięgu widzenia|Pokaż znaczniki|Linie pomocnicze|3D|UI|Etykiety|Nie pokazuj|Wariant A|Wariant B|Zezwól na obrót wieży myszą|Widok debugowania stref rozmieszczenia|Tylny punkt kontrolny widoczności|Przedni punkt kontrolny widoczności|Lewy boczny punkt kontrolny widoczności|Prawy boczny punkt kontrolny widoczności|Początkowy punkt kontrolny widoczności działa|Górny punkt kontrolny widoczności / port zasięgu widzenia|Punkt kontrolny widoczności działa / port zasięgu widzenia'.split(u'|'),
    'pt': u'Pontos de detecção|Definições dos pontos de detecção e portas de visão|Pontos de detecção e portas de visão|Pontos de detecção|Portas de visão|Mostrar marcadores|Guias|3D|IU|Rótulos|Não mostrar|Variante A|Variante B|Permitir girar a torre com o rato|Desenho de depuração das zonas de posicionamento|Ponto de detecção traseiro|Ponto de detecção dianteiro|Ponto de detecção lateral esquerdo|Ponto de detecção lateral direito|Ponto de detecção inicial do canhão|Ponto de detecção superior / porta de visão|Ponto de detecção do canhão / porta de visão'.split(u'|'),
    'ro': u'Puncte de control al vizibilității|Setări pentru punctele de control al vizibilității și punctele de vizualizare|Puncte de control al vizibilității și puncte de vizualizare|Puncte de control al vizibilității|Puncte de vizualizare|Afișează marcajele|Ghidaje|3D|IU|Etichete|Nu afișa|Varianta A|Varianta B|Permite rotirea turelei cu mouse-ul|Afișare de depanare a zonelor de plasare|Punct de control posterior al vizibilității|Punct de control frontal al vizibilității|Punct de control lateral stânga al vizibilității|Punct de control lateral dreapta al vizibilității|Punct de control inițial al vizibilității tunului|Punct de control superior al vizibilității / punct de vizualizare|Punct de control al vizibilității tunului / punct de vizualizare'.split(u'|'),
    'ru': u'Габаритные точки|Настройки габаритных и обзорных точек|Габаритные и обзорные точки|Габаритные точки|Обзорные точки|Отображать маркеры|Направляющие|3D|UI|Сноски|Не отображать|Вариант А|Вариант Б|Разрешить вращение башни мышью|Отладочная отрисовка зон размещения|Задняя габаритная|Передняя габаритная|Левая бортовая габаритная|Правая бортовая габаритная|Исходная орудийная габаритная|Верхняя обзорно-габаритная|Орудийная обзорно-габаритная'.split(u'|'),
    'sr': u'Tačke vidljivosti|Podešavanja tačaka vidljivosti i osmatračkih tačaka|Tačke vidljivosti i osmatračke tačke|Tačke vidljivosti|Osmatračke tačke|Prikaži oznake|Vođice|3D|UI|Natpisi|Ne prikazuj|Varijanta A|Varijanta B|Dozvoli okretanje kupole mišem|Prikaz zona postavljanja za otklanjanje grešaka|Zadnja tačka vidljivosti|Prednja tačka vidljivosti|Leva bočna tačka vidljivosti|Desna bočna tačka vidljivosti|Početna tačka vidljivosti topa|Gornja tačka vidljivosti / osmatračka tačka|Tačka vidljivosti topa / osmatračka tačka'.split(u'|'),
    'sv': u'Synlighetskontrollpunkter|Inställningar för synlighetskontroll- och observationspunkter|Synlighetskontroll- och observationspunkter|Synlighetskontrollpunkter|Observationspunkter|Visa markörer|Hjälplinjer|3D|UI|Etiketter|Visa inte|Variant A|Variant B|Tillåt tornrotation med musen|Felsökningsvisning av placeringszoner|Bakre synlighetskontrollpunkt|Främre synlighetskontrollpunkt|Vänster synlighetskontrollpunkt|Höger synlighetskontrollpunkt|Fast synlighetskontrollpunkt vid kanonen|Övre synlighetskontrollpunkt / observationspunkt|Kanonens synlighetskontrollpunkt / observationspunkt'.split(u'|'),
    'tr': u'Görüş kontrol noktaları|Görüş kontrol noktaları ve görüş menzili yuvaları ayarları|Görüş kontrol noktaları ve görüş menzili yuvaları|Görüş kontrol noktaları|Görüş menzili yuvaları|İşaretçileri göster|Kılavuzlar|3D|UI|Etiketler|Gösterme|A seçeneği|B seçeneği|Fareyle kule döndürmeye izin ver|Yerleşim bölgelerinin hata ayıklama çizimi|Arka görüş kontrol noktası|Ön görüş kontrol noktası|Sol yan görüş kontrol noktası|Sağ yan görüş kontrol noktası|Topun başlangıç görüş kontrol noktası|Üst görüş kontrol noktası / görüş menzili yuvası|Topun görüş kontrol noktası / görüş menzili yuvası'.split(u'|'),
    'uk': u'Габаритні точки|Налаштування габаритних і оглядових точок|Габаритні та оглядові точки|Габаритні точки|Оглядові точки|Показувати маркери|Напрямні|3D|UI|Підписи|Не показувати|Варіант А|Варіант Б|Дозволити обертання башти мишею|Налагоджувальне малювання зон розміщення|Задня габаритна|Передня габаритна|Ліва бортова габаритна|Права бортова габаритна|Початкова гарматна габаритна|Верхня оглядово-габаритна|Гарматна оглядово-габаритна'.split(u'|'),
}


def normalizeLanguage(language):
    if language is None:
        return DEFAULT_LANGUAGE
    try:
        language = language.decode('ascii')
    except AttributeError:
        pass
    except UnicodeDecodeError:
        return DEFAULT_LANGUAGE
    code = language.strip().lower().replace('-', '_')
    if code in _TRANSLATIONS:
        return code
    baseCode = code.split('_', 1)[0]
    return baseCode if baseCode in _TRANSLATIONS else DEFAULT_LANGUAGE


def getClientLanguageCode():
    try:
        from helpers import getClientLanguage
    except ImportError:
        return DEFAULT_LANGUAGE
    return normalizeLanguage(getClientLanguage())


def _getTranslation(language=None):
    code = (getClientLanguageCode() if language is None
            else normalizeLanguage(language))
    return dict(zip(_KEYS, _TRANSLATIONS[code]))


def getModListLabels(language=None):
    translation = _getTranslation(language)
    return {
        'name': translation['modName'],
        'description': translation['modDescription'],
    }


def getSettingsLabels(language=None):
    translation = _getTranslation(language)
    keys = (
        'title', 'showMaskPoints', 'showSpotPoints', 'showUiPoints',
        'showGuides', 'group3d', 'groupUi', 'callouts',
        'allowTurretRotation', 'layoutDebug',
    )
    labels = dict((key, translation[key]) for key in keys)
    labels['calloutModes'] = [
        translation['calloutOff'],
        translation['calloutA'],
        translation['calloutB'],
    ]
    return labels


def getMarkerLabels(language=None):
    translation = _getTranslation(language)
    return dict((key, translation[key]) for key in (
        'rear', 'front', 'left', 'right', 'gunStatic', 'top', 'gunMoving'))
