import logging

import BigWorld
import GUI
import math_utils
from AvatarInputHandler import cameras
from gui.shared import EVENT_BUS_SCOPE, g_eventBus
from gui.shared.event_bus import EventPriority
from gui.hangar_cameras.hangar_camera_common import CameraRelatedEvents
from gun_rotation_shared import calcPitchLimitsFromDesc
from helpers import dependency
from skeletons.gui.turret_gun_angles import ITurretAndGunAngles
from vehicle_systems.tankStructure import (
    TankNodeNames, TankPartIndexes, TankPartNames)

from .rotation_math import (
    canStartPartDrag, findRotatingPartHit, getDragAxes, nextAngles)

log = logging.getLogger('WOTSTAT_SPOTTING_POINTS')


class TurretMouseControl(object):
    def __init__(self, hangar):
        self._hangar = hangar
        self._angles = dependency.instance(ITurretAndGunAngles)
        self._enabled = False
        self._dragVehicle = None
        self._dragPart = None
        self._restrictionAdded = False

    def setEnabled(self, enabled):
        enabled = bool(enabled)
        if enabled == self._enabled:
            return
        self._enabled = enabled
        if enabled:
            self._hangar.onMouseDown += self._onMouseDown
            self._hangar.onMouseUp += self._onMouseUp
            self._hangar.onVehicleChangeStarted += self._onVehicleChangeStarted
        else:
            self.cancelDrag()
            self._hangar.onMouseDown -= self._onMouseDown
            self._hangar.onMouseUp -= self._onMouseUp
            self._hangar.onVehicleChangeStarted -= self._onVehicleChangeStarted

    def cancelDrag(self):
        self._dragVehicle = None
        self._dragPart = None
        if self._restrictionAdded:
            g_eventBus.removeRestriction(
                CameraRelatedEvents.LOBBY_VIEW_MOUSE_MOVE,
                self._restrictMouseMove, EVENT_BUS_SCOPE.GLOBAL)
            self._restrictionAdded = False

    def destroy(self):
        self.setEnabled(False)

    def _onMouseDown(self):
        if not self._enabled or not self._hangar.spaceInited:
            return
        if not self._hangar.isCursorOver3DScene:
            return
        vehicle = self._hangar.getVehicleEntity()
        if not self._isReady(vehicle):
            return
        hit = self._getRotatingPartHit(vehicle)
        if hit is None:
            return
        partIndex, _ = hit
        gun = vehicle.typeDescriptor.gun
        canRotateYaw = gun.staticTurretYaw is None
        canRotatePitch = gun.staticPitch is None
        if not canStartPartDrag(
                partIndex, TankPartIndexes.TURRET, TankPartIndexes.GUN,
                canRotateYaw, canRotatePitch):
            return
        self._dragVehicle = vehicle
        self._dragPart = partIndex
        if not self._restrictionAdded:
            g_eventBus.addRestriction(
                CameraRelatedEvents.LOBBY_VIEW_MOUSE_MOVE,
                self._restrictMouseMove, EVENT_BUS_SCOPE.GLOBAL,
                EventPriority.HIGH)
            self._restrictionAdded = True

    def _onMouseUp(self):
        self.cancelDrag()

    def _onVehicleChangeStarted(self):
        self.cancelDrag()

    def _restrictMouseMove(self, event):
        if self._dragVehicle is None:
            return True
        try:
            self._rotate(event.ctx)
        except Exception:
            log.exception('Turret drag stopped after rotation error')
            self.cancelDrag()
        return False

    def _rotate(self, ctx):
        vehicle = self._dragVehicle
        if vehicle is not self._hangar.getVehicleEntity() or not self._isReady(vehicle):
            self.cancelDrag()
            return
        appearance = vehicle.appearance
        descriptor = vehicle.typeDescriptor
        gun = descriptor.gun
        yaw = appearance.turretRotator.turretYaw
        pitch = self._getGunPitch(appearance)
        dx = float(ctx.get('dx', 0.0) or 0.0)
        dy = float(ctx.get('dy', 0.0) or 0.0)
        canRotateYaw = gun.staticTurretYaw is None
        canRotatePitch = gun.staticPitch is None
        rotateYaw, rotatePitch = getDragAxes(
            self._dragPart, TankPartIndexes.TURRET, TankPartIndexes.GUN,
            canRotateYaw, canRotatePitch)
        temporaryYaw, _ = nextAngles(
            yaw, pitch, dx, 0.0, gun.turretYawLimits,
            (-1000.0, 1000.0), changeYaw=rotateYaw, changePitch=False)
        pitchLimits = calcPitchLimitsFromDesc(
            temporaryYaw, gun.pitchLimits,
            descriptor.hull.turretPitches[0],
            descriptor.turret.gunJointPitch)
        nextYaw, nextPitch = nextAngles(
            yaw, pitch, dx, dy, gun.turretYawLimits, pitchLimits,
            changeYaw=rotateYaw, changePitch=rotatePitch)
        if rotateYaw:
            appearance.turretRotator.start(nextYaw, 0.0)
        if rotatePitch:
            self._setGunPitch(appearance, nextPitch)
        if rotateYaw or rotatePitch:
            self._angles.set(gunPitch=nextPitch, turretYaw=nextYaw)

    @staticmethod
    def _isReady(vehicle):
        return (vehicle is not None and getattr(vehicle, 'isVehicleLoaded', False)
                and getattr(vehicle, 'appearance', None) is not None
                and getattr(vehicle, 'typeDescriptor', None) is not None
                and vehicle.appearance.turretRotator is not None
                and vehicle.appearance.collisions is not None)

    @staticmethod
    def _getRotatingPartHit(vehicle):
        cursor = GUI.mcursor().position
        ray, start = cameras.getWorldRayAndPoint(cursor.x, cursor.y)
        ray.normalise()
        end = start + ray.scale(BigWorld.projection().farPlane)
        collisions = vehicle.appearance.collisions
        hits = collisions.collideAllWorld(start, end)
        if not hits:
            return None
        maxStaticPartIndex = getattr(
            collisions, 'maxStaticPartIndex', TankPartIndexes.ALL[-1])
        return findRotatingPartHit(
            [(hit[3], hit[0]) for hit in hits], maxStaticPartIndex,
            TankPartIndexes.TURRET, TankPartIndexes.GUN)

    @staticmethod
    def _getGunNode(appearance):
        node = appearance.compoundModel.node(TankNodeNames.GUN_INCLINATION)
        if node is None:
            node = appearance.compoundModel.node(TankPartNames.GUN)
        return node

    @classmethod
    def _getGunPitch(cls, appearance):
        if hasattr(appearance, 'getGunPitch'):
            return appearance.getGunPitch()
        return cls._getGunNode(appearance).local.pitch

    @classmethod
    def _setGunPitch(cls, appearance, pitch):
        if hasattr(appearance, 'rotateGunForAngle'):
            appearance.rotateGunForAngle(pitch)
            return
        matrix = math_utils.createRotationMatrix((0.0, pitch, 0.0))
        cls._getGunNode(appearance).local = matrix
