import math

ROTATION_PER_PIXEL = 0.003


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
    if partIndex in (turretIndex, gunIndex):
        return bool(canRotateYaw), bool(canRotatePitch)
    return False, False


def canStartPartDrag(partIndex, turretIndex, gunIndex, canRotateYaw,
                     canRotatePitch):
    return (partIndex in (turretIndex, gunIndex)
            and bool(canRotateYaw or canRotatePitch))


def nextAngles(yaw, pitch, dx, dy, yawLimits, pitchLimits,
               sensitivity=ROTATION_PER_PIXEL, changeYaw=True,
               changePitch=True):
    if changeYaw:
        yaw -= dx * sensitivity
        if yawLimits is None:
            yaw = normalizeAngle(yaw)
        else:
            yaw = clamp(yaw, yawLimits)
    if changePitch:
        pitch = clamp(pitch + dy * sensitivity, pitchLimits)
    return yaw, pitch
