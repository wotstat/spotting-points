import logging

import BigWorld
from ClientSelectableCameraVehicle import ClientSelectableCameraVehicle
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace

from .renderer import drawVehicle

log = logging.getLogger('WOTSTAT_SPOTTING_POINTS')


class SpottingPointsController(object):
    def __init__(self):
        self.enabled = False
        self._callbackId = None
        self._hangar = dependency.instance(IHangarSpace)
        self._hangar.onSpaceCreate += self._onSpaceCreate
        self._hangar.onSpaceDestroy += self._onSpaceDestroy

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self._start()
        else:
            self._stop()
        log.info('Display %s', 'enabled' if self.enabled else 'disabled')

    def destroy(self):
        self.enabled = False
        self._stop()
        self._hangar.onSpaceCreate -= self._onSpaceCreate
        self._hangar.onSpaceDestroy -= self._onSpaceDestroy

    def _onSpaceCreate(self):
        self._start()

    def _onSpaceDestroy(self, *args):
        self._stop()

    def _start(self):
        if self.enabled and self._callbackId is None and self._hangar.spaceInited:
            self._callbackId = BigWorld.callback(0.0, self._draw)

    def _stop(self):
        if self._callbackId is not None:
            BigWorld.cancelCallback(self._callbackId)
            self._callbackId = None

    def _draw(self):
        self._callbackId = None
        if not self.enabled or not self._hangar.spaceInited:
            return
        vehicle = self._hangar.getVehicleEntity()
        try:
            if (isinstance(vehicle, ClientSelectableCameraVehicle)
                    and vehicle.isVehicleLoaded and vehicle.appearance is not None
                    and vehicle.typeDescriptor is not None):
                drawVehicle(vehicle)
        except Exception:
            # Stop on a broken client contract rather than logging every frame.
            self.enabled = False
            log.exception('Display stopped after rendering error')
            return
        self._callbackId = BigWorld.callback(0.0, self._draw)
