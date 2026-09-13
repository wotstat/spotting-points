import GUI
from Math import Matrix, MatrixProduct
from realm import CURRENT_REALM
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS as GAME_VIEW_ALIAS
from gui.Scaleform.framework import ScopeTemplates, ViewSettings, g_entitiesFactories
from gui.Scaleform.framework.entities.View import View, ViewKey
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader
from skeletons.gui.impl import IGuiLoader
from vehicle_systems.tankStructure import TankNodeNames

from .marker_logic import buildOverlayData, isOverlaySceneActive

VIEW_ALIAS = 'wotstatSpottingPointsMarkerOverlay'
VIEW_SWF = 'wotstatSpottingPointsMarkers.swf'

_controller = None
_view = None
_loading = False
_registered = False
_RESTRICTED_LAYERS = set((
    WindowLayer.FULLSCREEN_WINDOW, WindowLayer.OVERLAY,
    WindowLayer.SUB_VIEW, WindowLayer.TOP_SUB_VIEW))
_BASE_WINDOW_CLASSES = set(('MainWindow', 'HangarWindow'))
if CURRENT_REALM == 'RU':
    _BASE_WINDOW_CLASSES.add('PopOverWindow')


def _getWindowAlias(window):
    try:
        return window.loadParams.viewKey.alias
    except AttributeError:
        return getattr(getattr(window, 'content', None), 'alias', None)


def _isBaseHangarWindow(window):
    return (_getWindowAlias(window) == GAME_VIEW_ALIAS.LOBBY_HANGAR
            or window.__class__.__name__ in _BASE_WINDOW_CLASSES)


def _getApp():
    return dependency.instance(IAppLoader).getDefLobbyApp()


def _createNativeMarker():
    markerClass = getattr(GUI, 'HangarVehicleMarker', None)
    if markerClass is None:
        markerClass = GUI.WGHangarVehicleMarker
    return markerClass()


def _createMarkerProvider(marker, vehicle):
    if marker.id == 'gunMoving':
        gunJoint = vehicle.model.node(TankNodeNames.GUN_JOINT)
        if gunJoint is not None:
            return gunJoint
    inverseVehicleMatrix = Matrix(vehicle.matrix)
    inverseVehicleMatrix.invert()
    localPoint = inverseVehicleMatrix.applyPoint(marker.point)
    localMatrix = Matrix()
    localMatrix.setTranslate(localPoint)
    provider = MatrixProduct()
    provider.a = localMatrix
    provider.b = vehicle.matrix
    return provider


def registerMarkerView():
    global _registered
    if _registered:
        return
    g_entitiesFactories.addSettings(ViewSettings(
        VIEW_ALIAS, MarkerOverlayView, VIEW_SWF, WindowLayer.MARKER, None,
        ScopeTemplates.DEFAULT_SCOPE))
    _registered = True


def unregisterMarkerView():
    global _controller, _view, _loading, _registered
    if _view is not None:
        _view.destroy()
    _view = None
    _controller = None
    _loading = False
    if _registered:
        g_entitiesFactories.removeSettings(VIEW_ALIAS)
        _registered = False


def showMarkerView(controller):
    global _controller, _loading
    app = _getApp()
    if app is None or app.containerManager is None:
        return False
    existing = app.containerManager.getViewByKey(ViewKey(VIEW_ALIAS))
    _controller = controller
    if existing is not None:
        controller.attachMarkerView(existing)
        return True
    if _loading:
        return True
    _loading = True
    app.loadView(SFViewLoadParams(VIEW_ALIAS))
    return True


def hideMarkerView(controller=None):
    global _controller, _view, _loading
    if controller is not None and _controller is not controller:
        return
    view = _view
    _view = None
    _controller = None
    _loading = False
    if view is not None:
        view.destroy()


class MarkerOverlayView(View):
    def __init__(self, ctx=None):
        super(MarkerOverlayView, self).__init__(ctx)
        self._controller = None
        self._ready = False
        self._windowsManager = None
        self._sceneActive = False
        self._nativeMarkers = {}

    def _populate(self):
        global _view, _loading
        super(MarkerOverlayView, self)._populate()
        _view = self
        _loading = False
        self._controller = _controller
        if self._controller is None:
            self.destroy()
            return
        self._ready = True
        self._windowsManager = dependency.instance(IGuiLoader).windowsManager
        self._windowsManager.onWindowStatusChanged += self._onWindowStatusChanged
        self._refreshSceneActive()
        self._controller.attachMarkerView(self)

    def updateMarkers(self, markers, vehicle, hoveredPointId):
        if not self._ready:
            return
        seen = set()
        for marker in markers:
            seen.add(marker.id)
            if marker.id in self._nativeMarkers:
                continue
            flashMarker = self.flashObject.as_createMarker(
                marker.id, marker.label)
            nativeMarker = _createNativeMarker()
            nativeMarker.setMarker(
                flashMarker, _createMarkerProvider(marker, vehicle))
            nativeMarker.markerSetActive(self._sceneActive)
            self._nativeMarkers[marker.id] = nativeMarker
        for pointId in tuple(self._nativeMarkers):
            if pointId not in seen:
                self._removeMarker(pointId)
        self.flashObject.as_updateMarkers(
            buildOverlayData(markers), hoveredPointId)

    def updateSceneActive(self):
        return self._ready and self._sceneActive

    def _onWindowStatusChanged(self, uniqueId, status):
        self._refreshSceneActive()

    def _refreshSceneActive(self):
        if self._windowsManager is None:
            return
        windows = self._windowsManager.findWindows(lambda window: True)
        hasHangar = any(_getWindowAlias(window) ==
                        GAME_VIEW_ALIAS.LOBBY_HANGAR for window in windows)
        hasBlockingWindow = any(
            window.layer in _RESTRICTED_LAYERS
            and not _isBaseHangarWindow(window) for window in windows)
        active = isOverlaySceneActive(hasHangar, hasBlockingWindow)
        if self._sceneActive != active:
            self._sceneActive = active
            self.flashObject.as_setActive(active)
            for marker in self._nativeMarkers.values():
                marker.markerSetActive(active)

    def hitTest(self, cursorX, cursorY):
        if not self._ready:
            return None
        pointId = self.flashObject.as_hitTest(cursorX, cursorY)
        return str(pointId) if pointId is not None else None

    def clearMarkers(self):
        if not self._ready:
            return
        for pointId in tuple(self._nativeMarkers):
            self._removeMarker(pointId)
        self.flashObject.as_clearMarkers()

    def _removeMarker(self, pointId):
        marker = self._nativeMarkers.pop(pointId, None)
        if marker is not None:
            marker.markerSetActive(False)
        self.flashObject.as_removeMarker(pointId)

    def _dispose(self):
        global _view, _loading
        controller = self._controller
        if self._ready:
            self.clearMarkers()
        self._ready = False
        self._controller = None
        if self._windowsManager is not None:
            self._windowsManager.onWindowStatusChanged -= self._onWindowStatusChanged
            self._windowsManager = None
        self._sceneActive = False
        self._nativeMarkers = None
        if _view is self:
            _view = None
        _loading = False
        if controller is not None:
            controller.detachMarkerView(self)
        super(MarkerOverlayView, self)._dispose()
