import math

ROTATION_PER_PIXEL = 0.0015


def clamp(value, limits):
    return max(limits[0], min(limits[1], value))


def normalizeAngle(value):
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def nextAngles(yaw, pitch, dx, dy, yawLimits, pitchLimits,
               sensitivity=ROTATION_PER_PIXEL):
    yaw -= dx * sensitivity
    if yawLimits is None:
        yaw = normalizeAngle(yaw)
    else:
        yaw = clamp(yaw, yawLimits)
    pitch = clamp(pitch + dy * sensitivity, pitchLimits)
    return yaw, pitch
