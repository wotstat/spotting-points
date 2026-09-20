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
# A compact ordered table keeps every locale easy to audit for missing fields.
_TRANSLATIONS = {
    'be': u'Габарытныя кропкі|Налады габарытных і аглядных кропак|Габарытныя і аглядныя кропкі|Габарытныя кропкі|Аглядныя кропкі|Паказваць маркеры|Накіравальныя|3D|UI|Подпісы|Не паказваць|Варыянт А|Варыянт Б|Дазволіць варочаць вежу мышшу|Адладачная адмалёўка зон размяшчэння|Задняя габарытная|Пярэдняя габарытная|Левая бартавая габарытная|Правая бартавая габарытная|Пачатковая гарматная габарытная|Верхняя аглядна-габарытная|Гарматная аглядна-габарытная'.split(u'|'),
    'bg': u'Контурни точки|Настройки на контурните и обзорните точки|Контурни и обзорни точки|Контурни точки|Обзорни точки|Показване на маркерите|Водачи|3D|UI|Етикети|Без показване|Вариант A|Вариант B|Разрешаване на въртенето на кулата с мишката|Отладъчно изчертаване на зоните за разполагане|Задна контурна|Предна контурна|Лява странична контурна|Дясна странична контурна|Изходна оръдейна контурна|Горна обзорно-контурна|Оръдейна обзорно-контурна'.split(u'|'),
    'cs': u'Body obrysu|Nastavení bodů obrysu a pozorovacích bodů|Body obrysu a pozorovací body|Body obrysu|Pozorovací body|Zobrazit značky|Vodicí čáry|3D|UI|Popisky|Nezobrazovat|Varianta A|Varianta B|Povolit otáčení věže myší|Ladicí vykreslení zón umístění|Zadní bod obrysu|Přední bod obrysu|Levý boční bod obrysu|Pravý boční bod obrysu|Výchozí bod obrysu děla|Horní pozorovací bod|Pozorovací bod děla'.split(u'|'),
    'da': u'Konturpunkter|Indstillinger for kontur- og observationspunkter|Kontur- og observationspunkter|Konturpunkter|Observationspunkter|Vis markører|Hjælpelinjer|3D|UI|Etiketter|Vis ikke|Variant A|Variant B|Tillad tårnrotation med musen|Fejlfindingsvisning af placeringszoner|Bageste konturpunkt|Forreste konturpunkt|Venstre konturpunkt|Højre konturpunkt|Fast konturpunkt ved kanonen|Øverste observationspunkt|Kanonens observationspunkt'.split(u'|'),
    'de': u'Umrisspunkte|Einstellungen für Umriss- und Beobachtungspunkte|Umriss- und Beobachtungspunkte|Umrisspunkte|Beobachtungspunkte|Markierungen anzeigen|Hilfslinien|3D|UI|Beschriftungen|Nicht anzeigen|Variante A|Variante B|Turmdrehung mit der Maus erlauben|Debuganzeige der Platzierungszonen|Hinterer Umrisspunkt|Vorderer Umrisspunkt|Linker seitlicher Umrisspunkt|Rechter seitlicher Umrisspunkt|Fester Umrisspunkt am Geschütz|Oberer Beobachtungspunkt|Beobachtungspunkt am Geschütz'.split(u'|'),
    'el': u'Σημεία περιγράμματος|Ρυθμίσεις σημείων περιγράμματος και παρατήρησης|Σημεία περιγράμματος και παρατήρησης|Σημεία περιγράμματος|Σημεία παρατήρησης|Εμφάνιση δεικτών|Γραμμές οδήγησης|3D|UI|Ετικέτες|Να μην εμφανίζονται|Παραλλαγή A|Παραλλαγή B|Να επιτρέπεται η περιστροφή πύργου με το ποντίκι|Εμφάνιση αποσφαλμάτωσης ζωνών τοποθέτησης|Πίσω σημείο περιγράμματος|Μπροστινό σημείο περιγράμματος|Αριστερό πλευρικό σημείο|Δεξί πλευρικό σημείο|Σταθερό σημείο περιγράμματος πυροβόλου|Επάνω σημείο παρατήρησης|Σημείο παρατήρησης πυροβόλου'.split(u'|'),
    'en': u'Silhouette points|Configure silhouette and observation points|Silhouette and observation points|Silhouette points|Observation points|Show markers|Guides|3D|UI|Labels|Do not show|Variant A|Variant B|Allow mouse turret rotation|Debug drawing of placement zones|Rear silhouette point|Front silhouette point|Left-side silhouette point|Right-side silhouette point|Initial gun silhouette point|Upper observation point|Gun observation point'.split(u'|'),
    'es': u'Puntos de silueta|Ajustes de los puntos de silueta y observación|Puntos de silueta y observación|Puntos de silueta|Puntos de observación|Mostrar marcadores|Guías|3D|IU|Etiquetas|No mostrar|Variante A|Variante B|Permitir girar la torreta con el ratón|Dibujo de depuración de zonas de colocación|Punto de silueta trasero|Punto de silueta delantero|Punto de silueta lateral izquierdo|Punto de silueta lateral derecho|Punto de silueta inicial del cañón|Punto de observación superior|Punto de observación del cañón'.split(u'|'),
    'fi': u'Ääriviivapisteet|Ääriviiva- ja tähystyspisteiden asetukset|Ääriviiva- ja tähystyspisteet|Ääriviivapisteet|Tähystyspisteet|Näytä merkit|Apulinjat|3D|UI|Nimilaput|Älä näytä|Vaihtoehto A|Vaihtoehto B|Salli tornin kääntäminen hiirellä|Sijoitusalueiden virheenkorjauspiirto|Takimmainen ääriviivapiste|Etummainen ääriviivapiste|Vasen sivuääriviivapiste|Oikea sivuääriviivapiste|Tykin kiinteä ääriviivapiste|Ylempi tähystyspiste|Tykin tähystyspiste'.split(u'|'),
    'fr': u'Points de gabarit|Réglages des points de gabarit et d’observation|Points de gabarit et d’observation|Points de gabarit|Points d’observation|Afficher les marqueurs|Repères|3D|UI|Étiquettes|Ne pas afficher|Variante A|Variante B|Autoriser la rotation de la tourelle à la souris|Affichage de débogage des zones de placement|Point de gabarit arrière|Point de gabarit avant|Point de gabarit latéral gauche|Point de gabarit latéral droit|Point de gabarit initial du canon|Point d’observation supérieur|Point d’observation du canon'.split(u'|'),
    'hr': u'Točke obrisa|Postavke točaka obrisa i promatranja|Točke obrisa i promatranja|Točke obrisa|Točke promatranja|Prikaži oznake|Vodilice|3D|UI|Natpisi|Ne prikazuj|Varijanta A|Varijanta B|Dopusti okretanje kupole mišem|Prikaz zona postavljanja za otklanjanje pogrešaka|Stražnja točka obrisa|Prednja točka obrisa|Lijeva bočna točka obrisa|Desna bočna točka obrisa|Početna točka obrisa topa|Gornja točka promatranja|Točka promatranja topa'.split(u'|'),
    'hu': u'Körvonalpontok|Körvonal- és megfigyelési pontok beállításai|Körvonal- és megfigyelési pontok|Körvonalpontok|Megfigyelési pontok|Jelölők megjelenítése|Segédvonalak|3D|UI|Címkék|Ne jelenjen meg|A változat|B változat|Torony forgatása egérrel|Elhelyezési zónák hibakeresési rajza|Hátsó körvonalpont|Első körvonalpont|Bal oldali körvonalpont|Jobb oldali körvonalpont|Löveg kezdeti körvonalpontja|Felső megfigyelési pont|Löveg megfigyelési pontja'.split(u'|'),
    'it': u'Punti sagoma|Impostazioni dei punti sagoma e di osservazione|Punti sagoma e di osservazione|Punti sagoma|Punti di osservazione|Mostra indicatori|Linee guida|3D|UI|Etichette|Non mostrare|Variante A|Variante B|Consenti la rotazione della torretta con il mouse|Disegno di debug delle zone di posizionamento|Punto sagoma posteriore|Punto sagoma anteriore|Punto sagoma laterale sinistro|Punto sagoma laterale destro|Punto sagoma iniziale del cannone|Punto di osservazione superiore|Punto di osservazione del cannone'.split(u'|'),
    'lt': u'Kontūro taškai|Kontūro ir stebėjimo taškų nustatymai|Kontūro ir stebėjimo taškai|Kontūro taškai|Stebėjimo taškai|Rodyti žymeklius|Kreipiamosios|3D|UI|Etiketės|Nerodyti|A variantas|B variantas|Leisti sukti bokštelį pele|Išdėstymo zonų derinimo vaizdas|Galinis kontūro taškas|Priekinis kontūro taškas|Kairysis šoninis kontūro taškas|Dešinysis šoninis kontūro taškas|Pradinis pabūklo kontūro taškas|Viršutinis stebėjimo taškas|Pabūklo stebėjimo taškas'.split(u'|'),
    'lv': u'Kontūras punkti|Kontūras un novērošanas punktu iestatījumi|Kontūras un novērošanas punkti|Kontūras punkti|Novērošanas punkti|Rādīt marķierus|Palīglīnijas|3D|UI|Iezīmes|Nerādīt|A variants|B variants|Atļaut torņa pagriešanu ar peli|Izvietojuma zonu atkļūdošanas zīmējums|Aizmugurējais kontūras punkts|Priekšējais kontūras punkts|Kreisais sānu kontūras punkts|Labais sānu kontūras punkts|Sākotnējais lielgabala kontūras punkts|Augšējais novērošanas punkts|Lielgabala novērošanas punkts'.split(u'|'),
    'nl': u'Omtrekpunten|Instellingen voor omtrek- en observatiepunten|Omtrek- en observatiepunten|Omtrekpunten|Observatiepunten|Markeringen tonen|Hulplijnen|3D|UI|Labels|Niet tonen|Variant A|Variant B|Torenrotatie met de muis toestaan|Debugweergave van plaatsingszones|Achterste omtrekpunt|Voorste omtrekpunt|Linker omtrekpunt|Rechter omtrekpunt|Vast omtrekpunt van het kanon|Bovenste observatiepunt|Observatiepunt van het kanon'.split(u'|'),
    'no': u'Konturpunkter|Innstillinger for kontur- og observasjonspunkter|Kontur- og observasjonspunkter|Konturpunkter|Observasjonspunkter|Vis markører|Hjelpelinjer|3D|UI|Etiketter|Ikke vis|Variant A|Variant B|Tillat tårnrotasjon med musen|Feilsøkingsvisning av plasseringssoner|Bakre konturpunkt|Fremre konturpunkt|Venstre konturpunkt|Høyre konturpunkt|Fast konturpunkt ved kanonen|Øvre observasjonspunkt|Kanonens observasjonspunkt'.split(u'|'),
    'pl': u'Punkty obrysu|Ustawienia punktów obrysu i obserwacyjnych|Punkty obrysu i obserwacyjne|Punkty obrysu|Punkty obserwacyjne|Pokaż znaczniki|Linie pomocnicze|3D|UI|Etykiety|Nie pokazuj|Wariant A|Wariant B|Zezwól na obrót wieży myszą|Widok debugowania stref rozmieszczenia|Tylny punkt obrysu|Przedni punkt obrysu|Lewy boczny punkt obrysu|Prawy boczny punkt obrysu|Początkowy punkt obrysu działa|Górny punkt obserwacyjny|Punkt obserwacyjny działa'.split(u'|'),
    'pt': u'Pontos de contorno|Definições dos pontos de contorno e observação|Pontos de contorno e observação|Pontos de contorno|Pontos de observação|Mostrar marcadores|Guias|3D|IU|Rótulos|Não mostrar|Variante A|Variante B|Permitir girar a torre com o rato|Desenho de depuração das zonas de posicionamento|Ponto de contorno traseiro|Ponto de contorno dianteiro|Ponto de contorno lateral esquerdo|Ponto de contorno lateral direito|Ponto de contorno inicial do canhão|Ponto de observação superior|Ponto de observação do canhão'.split(u'|'),
    'ro': u'Puncte de contur|Setări pentru punctele de contur și observare|Puncte de contur și observare|Puncte de contur|Puncte de observare|Afișează marcajele|Ghidaje|3D|IU|Etichete|Nu afișa|Varianta A|Varianta B|Permite rotirea turelei cu mouse-ul|Afișare de depanare a zonelor de plasare|Punct de contur posterior|Punct de contur frontal|Punct de contur lateral stânga|Punct de contur lateral dreapta|Punct de contur inițial al tunului|Punct de observare superior|Punct de observare al tunului'.split(u'|'),
    'ru': u'Габаритные точки|Настройки габаритных и обзорных точек|Габаритные и обзорные точки|Габаритные точки|Обзорные точки|Отображать маркеры|Направляющие|3D|UI|Сноски|Не отображать|Вариант А|Вариант Б|Разрешить вращение башни мышью|Отладочная отрисовка зон размещения|Задняя габаритная|Передняя габаритная|Левая бортовая габаритная|Правая бортовая габаритная|Исходная орудийная габаритная|Верхняя обзорно-габаритная|Орудийная обзорно-габаритная'.split(u'|'),
    'sr': u'Tačke obrisa|Podešavanja tačaka obrisa i osmatranja|Tačke obrisa i osmatranja|Tačke obrisa|Tačke osmatranja|Prikaži oznake|Vođice|3D|UI|Natpisi|Ne prikazuj|Varijanta A|Varijanta B|Dozvoli okretanje kupole mišem|Prikaz zona postavljanja za otklanjanje grešaka|Zadnja tačka obrisa|Prednja tačka obrisa|Leva bočna tačka obrisa|Desna bočna tačka obrisa|Početna tačka obrisa topa|Gornja tačka osmatranja|Tačka osmatranja topa'.split(u'|'),
    'sv': u'Konturpunkter|Inställningar för kontur- och observationspunkter|Kontur- och observationspunkter|Konturpunkter|Observationspunkter|Visa markörer|Hjälplinjer|3D|UI|Etiketter|Visa inte|Variant A|Variant B|Tillåt tornrotation med musen|Felsökningsvisning av placeringszoner|Bakre konturpunkt|Främre konturpunkt|Vänster konturpunkt|Höger konturpunkt|Fast konturpunkt vid kanonen|Övre observationspunkt|Kanonens observationspunkt'.split(u'|'),
    'tr': u'Siluet noktaları|Siluet ve gözetleme noktaları ayarları|Siluet ve gözetleme noktaları|Siluet noktaları|Gözetleme noktaları|İşaretçileri göster|Kılavuzlar|3D|UI|Etiketler|Gösterme|A seçeneği|B seçeneği|Fareyle kule döndürmeye izin ver|Yerleşim bölgelerinin hata ayıklama çizimi|Arka siluet noktası|Ön siluet noktası|Sol yan siluet noktası|Sağ yan siluet noktası|Topun başlangıç siluet noktası|Üst gözetleme noktası|Top gözetleme noktası'.split(u'|'),
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
