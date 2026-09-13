OPTION_NAMES = ('showMaskPoints', 'showSpotPoints', 'showGuides',
                'allowTurretRotation')


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
                or self.showGuides)
