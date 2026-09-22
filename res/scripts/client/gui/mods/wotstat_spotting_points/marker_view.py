import logging
import math
import time

import BigWorld
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
from vehicle_systems.tankStructure import TankNodeNames, TankPartNames

from .marker_logic import buildOverlayData, isOverlaySceneActive
from .side_layout import SideLayoutSolver
from .layout_solver import CalloutLayoutSolver
from .callout_transition import CalloutTransitions

VIEW_ALIAS = 'wotstatSpottingPointsMarkerOverlay'
VIEW_SWF = 'wotstatSpottingPointsMarkers.swf'
VIEW_LAYER = WindowLayer.WINDOW

log = logging.getLogger('WOTSTAT_SPOTTING_POINTS')

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

_STYLE_PREVIEW_ALIAS_NAMES = set((
  'STYLE_PREVIEW', 'STYLE_PROGRESSION_PREVIEW',
  'STYLE_BUYING_PREVIEW', 'SHOWCASE_STYLE_BUYING_PREVIEW'))
_VEHICLE_SCENE_ALIASES = set((
  GAME_VIEW_ALIAS.LOBBY_HANGAR, GAME_VIEW_ALIAS.LOBBY_CUSTOMIZATION))

for _aliasName in dir(GAME_VIEW_ALIAS):
  if (_aliasName.endswith('VEHICLE_PREVIEW')
      or _aliasName in _STYLE_PREVIEW_ALIAS_NAMES
      or _aliasName == 'VEHICLE_HUB'):
    _VEHICLE_SCENE_ALIASES.add(getattr(GAME_VIEW_ALIAS, _aliasName))

_VEHICLE_SCENE_CONTENT_CLASSES = set((
  'CustomizationMainView', 'VehicleHubMainView'))

try:
  from gui.impl.gen import R
  _CUSTOMIZATION_LAYOUT_ID = (
    R.views.lobby.customization.CustomizationMainView())
except (AttributeError, ImportError):
  _CUSTOMIZATION_LAYOUT_ID = None


def _getWindowAlias(window):
  try:
    return window.loadParams.viewKey.alias
  except AttributeError:
    return getattr(getattr(window, 'content', None), 'alias', None)


def _isVehicleSceneWindow(window):
  if _getWindowAlias(window) in _VEHICLE_SCENE_ALIASES:
    return True

  content = getattr(window, 'content', None)
  return (content is not None
      and (_CUSTOMIZATION_LAYOUT_ID is not None
        and getattr(content, 'layoutID', None)
        == _CUSTOMIZATION_LAYOUT_ID
        or content.__class__.__name__
        in _VEHICLE_SCENE_CONTENT_CLASSES))


def _isBaseLobbyWindow(window):
  return (_isVehicleSceneWindow(window)
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


def _createPartMarkerProvider(point, partProvider):
  localMatrix = Matrix()
  localMatrix.setTranslate(point)
  provider = MatrixProduct()
  provider.a = localMatrix
  provider.b = partProvider

  return provider


def registerMarkerView():
  global _registered

  if _registered:
    return

  g_entitiesFactories.addSettings(ViewSettings(
    VIEW_ALIAS, MarkerOverlayView, VIEW_SWF, VIEW_LAYER, None,
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
    self._markerLayerView = None
    self._sceneActive = False
    self._nativeMarkers = {}
    self._layoutMarkers = {}
    self._hoverMarkers = {}
    self._initializeLayoutSolver()

  def _initializeLayoutSolver(self):
    self._layoutSolver = SideLayoutSolver()
    self._layoutTransitions = CalloutTransitions()
    self._layoutSolverFailed = False

  def solveLayout(self, payload):
    if self._layoutSolverFailed:
      return {'revision': self._layoutSolver.revision,
          'disabled': True}

    try:
      width, height, hull, turret, items = _convertLayoutPayload(
        payload)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
      return {'revision': self._layoutSolver.revision}

    try:
      result = self._layoutSolver.solve(
        width, height, hull, turret, items)
      return self._layoutTransitions.apply(result, time.clock())
    except Exception:
      self._layoutSolverFailed = True
      log.exception('Callout layout solver stopped after error')
      controller = self._controller

      if controller is not None:
        BigWorld.callback(
          0.0, lambda: self._disableUiPointsAfterFailure(controller))

      return {'revision': self._layoutSolver.revision,
          'disabled': True}

  def _disableUiPointsAfterFailure(self, controller):
    if self._controller is controller:
      controller.setOption('showUiPoints', False)

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

  def updateMarkers(self, markers, vehicle, hoveredPointId,
          layoutBounds=None, highlightGroup=None):
    if not self._ready:
      return

    if layoutBounds is not None:
      self._createLayoutMarkers(
        'hull', layoutBounds.hull,
        vehicle.model.node(TankPartNames.HULL))
      self._createLayoutMarkers(
        'turret', layoutBounds.turret,
        vehicle.model.node(TankPartNames.TURRET))

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

    self._updateHoverGeometry(vehicle, highlightGroup)
    self.flashObject.as_updateMarkers(
      buildOverlayData(markers), hoveredPointId)

  def _createLayoutMarkers(self, prefix, points, partProvider):
    if partProvider is None:
      return

    for index, point in enumerate(points):
      anchorId = '%s%d' % (prefix, index)

      if anchorId in self._layoutMarkers:
        continue

      flashMarker = self.flashObject.as_createLayoutAnchor(anchorId)
      nativeMarker = _createNativeMarker()
      nativeMarker.setMarker(
        flashMarker, _createPartMarkerProvider(point, partProvider))
      nativeMarker.markerSetActive(self._sceneActive)
      self._layoutMarkers[anchorId] = nativeMarker

  def _updateHoverGeometry(self, vehicle, highlightGroup):
    points = []
    pointIds = {}
    payload = []

    if highlightGroup is not None:
      for style, lines in (('faded', highlightGroup.faded),
                ('bright', highlightGroup.bright)):
        for line in lines:
          ids = []

          for point in line.points:
            key = tuple(round(float(point[index]), 6)
                  for index in range(3))
            anchorId = pointIds.get(key)

            if anchorId is None:
              anchorId = 'hover%d' % len(points)
              pointIds[key] = anchorId
              points.append(point)

            ids.append(anchorId)

          if len(ids) >= 2:
            payload.append({'style': style, 'points': ids})

    if points:
      inverseVehicleMatrix = Matrix(vehicle.matrix)
      inverseVehicleMatrix.invert()

      for index, point in enumerate(points):
        anchorId = 'hover%d' % index
        localPoint = inverseVehicleMatrix.applyPoint(point)
        localKey = tuple(round(float(localPoint[axis]), 6)
                for axis in range(3))
        entry = self._hoverMarkers.get(anchorId)

        if entry is None:
          flashMarker = self.flashObject.as_createHoverAnchor(anchorId)
          provider = _createPartMarkerProvider(
            localPoint, vehicle.matrix)
          nativeMarker = _createNativeMarker()
          nativeMarker.setMarker(flashMarker, provider)
          nativeMarker.markerSetActive(self._sceneActive)
          self._hoverMarkers[anchorId] = (
            nativeMarker, provider, localKey)
        elif entry[2] != localKey:
          provider = entry[1]
          localMatrix = Matrix()
          localMatrix.setTranslate(localPoint)
          provider.a = localMatrix
          provider.b = vehicle.matrix
          self._hoverMarkers[anchorId] = (
            entry[0], provider, localKey)

    for anchorId in tuple(self._hoverMarkers):
      if int(anchorId[5:]) >= len(points):
        self._removeHoverMarker(anchorId)

    self.flashObject.as_setHoverGeometry(payload)

  def updateSceneActive(self):
    return self._ready and self._sceneActive

  def setLayoutDebug(self, value):
    if self._ready:
      self.flashObject.as_setLayoutDebug(bool(value))

  def setCalloutMode(self, mode):
    self._layoutSolver = CalloutLayoutSolver() if mode == 2 else SideLayoutSolver()
    self._layoutSolverFailed = False

    if self._ready:
      self.flashObject.as_setCalloutsEnabled(mode != 0)

  def setTooltipsEnabled(self, value):
    if self._ready:
      self.flashObject.as_setTooltipsEnabled(bool(value))

  def _onWindowStatusChanged(self, uniqueId, status):
    self._refreshSceneActive()

  def _attachToMarkerLayer(self):
    # The Scaleform MARKER container is single-view. Loading our view there
    # would replace the game's marker view, so only move our display root
    # under the existing view and keep our lifecycle in the WINDOW layer.
    app = _getApp()

    if app is None or app.containerManager is None:
      self._markerLayerView = None
      return False

    markerLayerView = app.containerManager.getView(WindowLayer.MARKER)

    if markerLayerView is None:
      self._markerLayerView = None
      return False

    if self._markerLayerView is markerLayerView:
      return True

    markerFlash = getattr(markerLayerView, 'flashObject', None)
    overlayFlash = getattr(self, 'flashObject', None)

    if markerFlash is None or overlayFlash is None:
      return False

    try:
      markerFlash.addChild(overlayFlash)
    except (AttributeError, RuntimeError, TypeError, ValueError):
      log.exception(
        'Failed to attach UI markers to the hangar marker layer')
      return False

    self._markerLayerView = markerLayerView

    return True

  def _refreshSceneActive(self):
    if self._windowsManager is None:
      return

    attachedToMarkerLayer = self._attachToMarkerLayer()
    windows = self._windowsManager.findWindows(lambda window: True)
    hasVehicleScene = any(
      _isVehicleSceneWindow(window) for window in windows)
    hasBlockingWindow = any(
      window.layer in _RESTRICTED_LAYERS
      and not _isBaseLobbyWindow(window) for window in windows)
    active = (attachedToMarkerLayer and isOverlaySceneActive(
      hasVehicleScene, hasBlockingWindow))

    if self._sceneActive != active:
      self._sceneActive = active
      self.flashObject.as_setActive(active)

      for marker in self._nativeMarkers.values():
        marker.markerSetActive(active)

      for marker in self._layoutMarkers.values():
        marker.markerSetActive(active)

      for marker, provider, localKey in self._hoverMarkers.values():
        marker.markerSetActive(active)

  def hitTest(self, cursorX, cursorY):
    if not self._ready:
      return None

    pointId = self.flashObject.as_hitTest(cursorX, cursorY)
    return str(pointId) if pointId is not None else None

  def clearTooltipHover(self):
    if self._ready:
      self.flashObject.as_hideTooltip()

  def clearMarkers(self):
    if not self._ready:
      return

    self._layoutSolver.reset()
    self._layoutTransitions.reset()

    for pointId in tuple(self._nativeMarkers):
      self._removeMarker(pointId)

    for anchorId in tuple(self._layoutMarkers):
      marker = self._layoutMarkers.pop(anchorId)
      marker.markerSetActive(False)

    for anchorId in tuple(self._hoverMarkers):
      self._removeHoverMarker(anchorId)

    self.flashObject.as_clearMarkers()

  def _removeMarker(self, pointId):
    marker = self._nativeMarkers.pop(pointId, None)

    if marker is not None:
      marker.markerSetActive(False)

    self.flashObject.as_removeMarker(pointId)

  def _removeHoverMarker(self, anchorId):
    entry = self._hoverMarkers.pop(anchorId, None)

    if entry is not None:
      entry[0].markerSetActive(False)

    self.flashObject.as_removeHoverAnchor(anchorId)

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

    self._markerLayerView = None
    self._sceneActive = False
    self._nativeMarkers = None
    self._layoutMarkers = None
    self._hoverMarkers = None
    self._layoutSolver = None

    if _view is self:
      _view = None

    _loading = False

    if controller is not None:
      controller.detachMarkerView(self)

    super(MarkerOverlayView, self)._dispose()


def _readField(value, name):
  try:
    return getattr(value, name)
  except AttributeError:
    return value[name]


def _finiteNumber(value):
  number = float(value)

  if math.isnan(number) or math.isinf(number):
    raise ValueError('Expected finite layout number')

  return number


def _convertPoints(values):
  if len(values) != 8:
    raise ValueError('Expected eight projected corners')

  points = []

  for index in xrange(8):
    point = values[index]

    if len(point) != 2:
      raise ValueError('Expected projected point pair')

    points.append((_finiteNumber(point[0]), _finiteNumber(point[1])))

  return points


def _convertLayoutPayload(payload):
  width = _finiteNumber(_readField(payload, 'width'))
  height = _finiteNumber(_readField(payload, 'height'))

  if width <= 0.0 or height <= 0.0:
    raise ValueError('Expected positive viewport')

  hull = _convertPoints(_readField(payload, 'hull'))
  turret = _convertPoints(_readField(payload, 'turret'))

  # Native markers start at the same position until their first projection.
  # Do not seed solver hysteresis or transitions with that placeholder frame.
  for corners in (hull, turret):
    if len(set(corners)) < 3:
      raise ValueError('Waiting for native marker projection')

  values = _readField(payload, 'items')
  items = []
  seen = set()

  for index in xrange(len(values)):
    value = values[index]
    pointId = str(_readField(value, 'id'))
    part = str(_readField(value, 'part'))

    if not pointId or pointId in seen or part not in ('hull', 'turret'):
      raise ValueError('Invalid layout item identity')

    widthValue = _finiteNumber(_readField(value, 'width'))
    heightValue = _finiteNumber(_readField(value, 'height'))

    if widthValue <= 0.0 or heightValue <= 0.0:
      raise ValueError('Expected positive callout size')

    seen.add(pointId)
    items.append({
      'id': pointId,
      'x': _finiteNumber(_readField(value, 'x')),
      'y': _finiteNumber(_readField(value, 'y')),
      'width': widthValue,
      'height': heightValue,
      'part': part
    })

  items.sort(key=lambda item: item['id'])

  return width, height, hull, turret, items
