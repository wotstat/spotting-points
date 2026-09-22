OPTION_NAMES = ('showMaskPoints', 'showSpotPoints', 'showUiPoints',
        'showGuides', 'showTooltips', 'allowTurretRotation',
        'layoutDebug')
UI_FRAME_INTERVAL = 1.0 / 30.0


class DisplayOptions(object):
  def __init__(self):
    for name in OPTION_NAMES:
      setattr(self, name, False)

    self.showTooltips = True
    self.calloutMode = 0

  def setValue(self, name, value):
    if name == 'calloutMode':
      if value not in (0, 1, 2):
        return False

      self.calloutMode = int(value)
      return True

    if name not in OPTION_NAMES:
      return False

    setattr(self, name, bool(value))

    return True

  def asDict(self):
    result = dict((name, getattr(self, name)) for name in OPTION_NAMES)
    result['calloutMode'] = self.calloutMode
    return result

  def hasVisuals(self):
    return (self.showMaskPoints or self.showSpotPoints
        or self.showUiPoints or self.showGuides)

  def drawInterval(self, hasHover):
    if self.showMaskPoints or self.showSpotPoints or self.showGuides:
      return 0.0

    return UI_FRAME_INTERVAL if self.showUiPoints else 0.0
