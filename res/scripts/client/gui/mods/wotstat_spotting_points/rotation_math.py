import math

ROTATION_PER_PIXEL = 0.0015


def clamp(value, limits):
    return max(limits[0], min(limits[1], value))


def normalizeAngle(value):
    return value % (2.0 * math.pi)


def findRotatingPartHit(partHits, maxStaticPartIndex, turretIndex, gunIndex):
    for partIndex, distance in partHits:
        if partIndex > maxStaticPartIndex:
            continue
        if partIndex in (turretIndex, gunIndex):
            return partIndex, distance
        return None
    return None


def isRotatingPartHit(partIndices, maxStaticPartIndex, turretIndex, gunIndex):
    partHits = [(partIndex, None) for partIndex in partIndices]
    return findRotatingPartHit(
        partHits, maxStaticPartIndex, turretIndex, gunIndex) is not None


def getDragAxes(partIndex, turretIndex, gunIndex, canRotateYaw,
                canRotatePitch):
    if partIndex == turretIndex:
        return bool(canRotateYaw), False
    if partIndex == gunIndex:
        return bool(canRotateYaw), bool(canRotatePitch)
    return False, False


def canStartPartDrag(partIndex, turretIndex, gunIndex, canRotateYaw,
                     canRotatePitch):
    if partIndex == turretIndex:
        return bool(canRotateYaw)
    if partIndex == gunIndex:
        return bool(canRotatePitch)
    return False


def filterDragDeltas(dx, dy, rotateYaw, rotatePitch):
    return (dx if rotateYaw else 0.0,
            dy if rotatePitch else 0.0)


def nextAngles(yaw, pitch, dx, dy, yawLimits, pitchLimits,
               sensitivity=ROTATION_PER_PIXEL, changeYaw=True,
               changePitch=True, yawMultiplier=1.0, pitchMultiplier=1.0):
    if changeYaw:
        yaw -= dx * sensitivity * yawMultiplier
        if yawLimits is None:
            yaw = normalizeAngle(yaw)
        else:
            yaw = clamp(yaw, yawLimits)
    if changePitch:
        pitch = clamp(
            pitch + dy * sensitivity * pitchMultiplier, pitchLimits)
    return yaw, pitch
