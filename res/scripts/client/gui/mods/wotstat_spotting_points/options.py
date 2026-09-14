OPTION_NAMES = ('showMaskPoints', 'showSpotPoints', 'showUiPoints',
                'showGuides', 'allowTurretRotation', 'layoutDebug')
UI_FRAME_INTERVAL = 1.0 / 30.0


class DisplayOptions(object):
    def __init__(self):
        for name in OPTION_NAMES:
            setattr(self, name, False)

    def setValue(self, name, value):
        if name not in OPTION_NAMES:
            return False
        setattr(self, name, bool(value))
        return True

    def asDict(self):
        return dict((name, getattr(self, name)) for name in OPTION_NAMES)

    def hasVisuals(self):
        return (self.showMaskPoints or self.showSpotPoints
                or self.showUiPoints or self.showGuides)

    def drawInterval(self, hasHover):
        if (self.showMaskPoints or self.showSpotPoints or self.showGuides
                or hasHover):
            return 0.0
        return UI_FRAME_INTERVAL if self.showUiPoints else 0.0
