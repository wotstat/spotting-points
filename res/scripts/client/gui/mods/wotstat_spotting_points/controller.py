import logging

import BigWorld
import GUI
from ClientSelectableCameraVehicle import ClientSelectableCameraVehicle
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace

from .options import DisplayOptions
from .marker_logic import buildMarkerData
from .marker_view import hideMarkerView, showMarkerView
from .renderer import drawGeometry, getLayoutBounds, getWorldGeometry
from .settings_view import updateDisplayedOptions
from .turret_control import TurretMouseControl

log = logging.getLogger('WOTSTAT_SPOTTING_POINTS')


class SpottingPointsController(object):
    def __init__(self):
        self.options = DisplayOptions()
        self._callbackId = None
        self._hangar = dependency.instance(IHangarSpace)
        self._turretControl = TurretMouseControl(self._hangar)
        self._markerView = None
        self._hoveredPointId = None
        self._nextMarkerUpdate = 0.0
        self._hangar.onSpaceCreate += self._onSpaceCreate
        self._hangar.onSpaceDestroy += self._onSpaceDestroy
        self._hangar.onVehicleChangeStarted += self._onVehicleChangeStarted

    def getOptions(self):
        return self.options.asDict()

    def setOption(self, name, value):
        if not self.options.setValue(name, value):
            return False
        if name == 'allowTurretRotation':
            self._turretControl.setEnabled(self.options.allowTurretRotation)
        elif name == 'showUiPoints':
            if self.options.showUiPoints:
                self._nextMarkerUpdate = 0.0
                showMarkerView(self)
            else:
                self._hoveredPointId = None
                hideMarkerView(self)
        elif name == 'layoutDebug' and self._markerView is not None:
            self._markerView.setLayoutDebug(self.options.layoutDebug)
        elif name == 'calloutMode' and self._markerView is not None:
            self._markerView.setCalloutMode(self.options.calloutMode)
        elif name == 'showTooltips' and self._markerView is not None:
            self._markerView.setTooltipsEnabled(self.options.showTooltips)
        if self.options.hasVisuals():
            self._start()
        else:
            self._stop()
        log.info('Option %s=%s', name, value)
        return True

    def destroy(self):
        hideMarkerView(self)
        self._stop()
        self._turretControl.destroy()
        self._hangar.onSpaceCreate -= self._onSpaceCreate
        self._hangar.onSpaceDestroy -= self._onSpaceDestroy
        self._hangar.onVehicleChangeStarted -= self._onVehicleChangeStarted

    def _onSpaceCreate(self):
        if self.options.showUiPoints:
            showMarkerView(self)
        self._start()

    def _onSpaceDestroy(self, *args):
        self._stop()
        self._clearMarkerState()
        self._turretControl.cancelDrag()

    def _onVehicleChangeStarted(self, *args):
        self._clearMarkerState()

    def _clearMarkerState(self):
        self._hoveredPointId = None
        self._nextMarkerUpdate = 0.0
        if self._markerView is not None:
            self._markerView.clearMarkers()

    def attachMarkerView(self, view):
        self._markerView = view
        view.setLayoutDebug(self.options.layoutDebug)
        view.setCalloutMode(self.options.calloutMode)
        view.setTooltipsEnabled(self.options.showTooltips)

    def detachMarkerView(self, view):
        if self._markerView is view:
            self._markerView = None
        self._hoveredPointId = None

    def _start(self):
        if (self.options.hasVisuals() and self._callbackId is None
                and self._hangar.spaceInited):
            self._callbackId = BigWorld.callback(0.0, self._draw)

    def _stop(self):
        if self._callbackId is not None:
            BigWorld.cancelCallback(self._callbackId)
            self._callbackId = None

    def _draw(self):
        self._callbackId = None
        if not self.options.hasVisuals() or not self._hangar.spaceInited:
            return
        vehicle = self._hangar.getVehicleEntity()
        try:
            if (isinstance(vehicle, ClientSelectableCameraVehicle)
                    and vehicle.isVehicleLoaded and vehicle.appearance is not None
                    and vehicle.typeDescriptor is not None):
                now = BigWorld.time()
                updateUi = (self.options.showUiPoints
                            and self._markerView is not None
                            and now >= self._nextMarkerUpdate)
                needHighlight = (updateUi
                                 and self._hoveredPointId is not None)
                needLines = self.options.showGuides or needHighlight
                geometry = getWorldGeometry(
                    vehicle, needLines,
                    needHighlight
                    and self._hoveredPointId == 'gunMoving')
                if geometry is not None:
                    drawGeometry(
                        geometry, self.options.showMaskPoints,
                        self.options.showSpotPoints, self.options.showGuides,
                        self._hoveredPointId)
                    if updateUi:
                        self._nextMarkerUpdate = now + 1.0 / 30.0
                        try:
                            self._updateMarkerView(vehicle, geometry)
                        except Exception:
                            self._disableUiPointsAfterError()
                else:
                    self._clearMarkerState()
            else:
                self._clearMarkerState()
        except Exception:
            # Stop on a broken client contract rather than logging every frame.
            self.options.showMaskPoints = False
            self.options.showSpotPoints = False
            self.options.showUiPoints = False
            self.options.showGuides = False
            hideMarkerView(self)
            updateDisplayedOptions(self.options.asDict())
            log.exception('Display stopped after rendering error')
            return
        if self.options.hasVisuals():
            self._callbackId = BigWorld.callback(
                self.options.drawInterval(self._hoveredPointId is not None),
                self._draw)

    def _disableUiPointsAfterError(self):
        log.exception('UI markers stopped after rendering error')
        self.options.showUiPoints = False
        self._hoveredPointId = None
        try:
            hideMarkerView(self)
            updateDisplayedOptions(self.options.asDict())
        except Exception:
            log.exception('Failed to tear down broken UI markers')

    def _updateMarkerView(self, vehicle, geometry):
        if geometry is None:
            self._markerView.clearMarkers()
            return
        maskPoints, spotPoints, _, highlightGroups = geometry
        markers = buildMarkerData(maskPoints, spotPoints)
        layoutBounds = getLayoutBounds(vehicle)
        active = self._markerView.updateSceneActive()
        if active:
            self._markerView.updateMarkers(
                markers, vehicle, self._hoveredPointId, layoutBounds,
                highlightGroups.get(self._hoveredPointId))
        self._updateMarkerHover(active)

    def _updateMarkerHover(self, markerSceneActive):
        cursor = GUI.mcursor()
        if not markerSceneActive or not cursor.inWindow or not cursor.inFocus:
            self._hoveredPointId = None
            if self._markerView is not None:
                self._markerView.clearTooltipHover()
            return
        position = cursor.position
        self._hoveredPointId = self._markerView.hitTest(
            position.x, position.y)
