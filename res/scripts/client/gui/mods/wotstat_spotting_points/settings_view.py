# -*- coding: utf-8 -*-
import BigWorld
import Keys

from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import ScopeTemplates, ViewSettings, g_entitiesFactories
from gui.Scaleform.framework.entities.View import ViewKey
from gui.Scaleform.framework.entities.abstract.AbstractWindowView import AbstractWindowView
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader

VIEW_ALIAS = 'wotstatSpottingPointsSettings'
VIEW_SWF = 'wotstatSpottingPointsSettings.swf'

LABELS = {
    'title': 'Габаритные и обзорные точки',
    'showMaskPoints': 'Отображать габаритные точки',
    'showSpotPoints': 'Отображать обзорные точки',
    'showUiPoints': 'Отображать точки в UI',
    'showGuides': 'Отображать направляющие',
    'allowTurretRotation': 'Разрешить вращение башни мышью',
    'layoutDebug': 'Отладочная отрисовка зон размещения',
}

_controller = None
_window = None
_loading = False
_registered = False
_showDebugOption = False


def _getApp():
    return dependency.instance(IAppLoader).getDefLobbyApp()


def registerSettingsView():
    global _registered
    if _registered:
        return
    g_entitiesFactories.addSettings(ViewSettings(
        VIEW_ALIAS, SettingsWindow, VIEW_SWF, WindowLayer.WINDOW, None,
        ScopeTemplates.DEFAULT_SCOPE, isModal=False, canDrag=True,
        canClose=True, isCentered=True))
    _registered = True


def unregisterSettingsView():
    global _controller, _window, _loading, _registered, _showDebugOption
    if _window is not None:
        _window.destroy()
    _window = None
    _controller = None
    _loading = False
    _showDebugOption = False
    if _registered:
        g_entitiesFactories.removeSettings(VIEW_ALIAS)
        _registered = False


def showSettings(controller):
    global _controller, _loading, _showDebugOption
    app = _getApp()
    if app is None or app.containerManager is None:
        return False
    existing = app.containerManager.getViewByKey(ViewKey(VIEW_ALIAS))
    if existing is not None:
        existing.setActive(True)
        return True
    if _loading:
        return True
    _controller = controller
    _showDebugOption = (BigWorld.isKeyDown(Keys.KEY_LALT)
                        or BigWorld.isKeyDown(Keys.KEY_RALT))
    _loading = True
    app.loadView(SFViewLoadParams(VIEW_ALIAS))
    return True


def updateDisplayedOptions(options):
    if _window is not None:
        _window.flashObject.as_setOptions(options)


class SettingsWindow(AbstractWindowView):
    def __init__(self, ctx=None):
        super(SettingsWindow, self).__init__()
        self._controller = _controller
        self._showDebugOption = _showDebugOption

    def _populate(self):
        global _window, _loading
        super(SettingsWindow, self)._populate()
        _window = self
        _loading = False
        if self._controller is None:
            self.destroy()
            return
        self.flashObject.as_setData(
            self._controller.getOptions(), LABELS, self._showDebugOption)

    def optionChanged(self, name, value):
        if self._controller is not None:
            self._controller.setOption(str(name), bool(value))

    def onWindowClose(self):
        self.destroy()

    def _dispose(self):
        global _window, _loading, _showDebugOption
        _window = None
        _loading = False
        _showDebugOption = False
        self._controller = None
        self._showDebugOption = False
        super(SettingsWindow, self)._dispose()
