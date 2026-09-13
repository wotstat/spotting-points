import logging

import BigWorld
from ClientSelectableCameraVehicle import ClientSelectableCameraVehicle
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace

from .options import DisplayOptions
from .renderer import drawVehicle
from .turret_control import TurretMouseControl

log = logging.getLogger('WOTSTAT_SPOTTING_POINTS')


class SpottingPointsController(object):
    def __init__(self):
        self.options = DisplayOptions()
        self._callbackId = None
        self._hangar = dependency.instance(IHangarSpace)
        self._turretControl = TurretMouseControl(self._hangar)
        self._hangar.onSpaceCreate += self._onSpaceCreate
        self._hangar.onSpaceDestroy += self._onSpaceDestroy

    def getOptions(self):
        return self.options.asDict()

    def setOption(self, name, value):
        if not self.options.setValue(name, value):
            return False
        if name == 'allowTurretRotation':
            self._turretControl.setEnabled(self.options.allowTurretRotation)
        if self.options.hasVisuals():
            self._start()
        else:
            self._stop()
        log.info('Option %s=%s', name, bool(value))
        return True

    def destroy(self):
        self._stop()
        self._turretControl.destroy()
        self._hangar.onSpaceCreate -= self._onSpaceCreate
        self._hangar.onSpaceDestroy -= self._onSpaceDestroy

    def _onSpaceCreate(self):
        self._start()

    def _onSpaceDestroy(self, *args):
        self._stop()
        self._turretControl.cancelDrag()

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
                drawVehicle(vehicle, self.options.showMaskPoints,
                            self.options.showSpotPoints,
                            self.options.showGuides)
        except Exception:
            # Stop on a broken client contract rather than logging every frame.
            self.options.showMaskPoints = False
            self.options.showSpotPoints = False
            self.options.showGuides = False
            log.exception('Display stopped after rendering error')
            return
        self._callbackId = BigWorld.callback(0.0, self._draw)
