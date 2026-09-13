from DebugDrawer import DebugDrawer
from Math import Matrix, Vector3
from realm import CURRENT_REALM
from vehicle_systems.tankStructure import TankPartIndexes, TankNodeNames

from .geometry import (
    addMovingGunPoint, buildGeometry, LineGeometry, selectGeometry)

MASK_COLORS = (0xff3135, 0xab6d67)
SPOT_COLORS = (0x00aaff, 0x5990bf)
# The clients submit DebugDrawer primitives in opposite order.
PASSES = (False, True) if CURRENT_REALM == 'RU' else (True, False)


def drawSphere(drawer, point, radius, colors):
    for front in PASSES:
        sphere = drawer.sphere()
        sphere.position(point)
        sphere.radius(radius)
        sphere.colour(colors[0 if front else 1])
        sphere.zTest(front)
        sphere.zWrite(front)


def drawLine(drawer, geometry):
    for front in PASSES if geometry.backColor is not None else (True,):
        line = drawer.line()
        line.colour(geometry.color if front else geometry.backColor)
        if not front:
            line.zTest(False)
            line.zWrite(False)
        line.points(geometry.points)


def getWorldGeometry(vehicle):
    appearance = vehicle.appearance
    collisions = appearance.collisions
    if collisions is None:
        return None
    # Read the same local collision boxes as model_assembler.setupCollisions,
    # without modifying the shared vehicle descriptor/hit testers.
    hullBounds = collisions.getBoundingBox(TankPartIndexes.HULL)
    turretBounds = collisions.getBoundingBox(TankPartIndexes.TURRET)
    if not hullBounds or not turretBounds:
        return None
    descr = vehicle.typeDescriptor
    hullOffset = descr.chassis.hullPosition
    turretOffset = descr.hull.turretPositions[0]
    points, lines = buildGeometry(hullBounds, turretBounds, hullOffset,
                                 turretOffset, descr.turret.gunPosition)
    matrix = Matrix(vehicle.matrix)
    maskPoints = [matrix.applyPoint(Vector3(p)) for p in points]
    worldLines = [LineGeometry([matrix.applyPoint(Vector3(p)) for p in line.points],
                              line.color, line.backColor) for line in lines]

    # This model node already includes actual turret rotation, yaw limits,
    # static angles and customization animations in both clients.
    gunJoint = vehicle.model.node(TankNodeNames.GUN_JOINT)
    if gunJoint is None:
        return None
    movingPoint = Vector3(gunJoint.position)
    maskPoints, spotPoints = addMovingGunPoint(
        maskPoints, [maskPoints[5]], movingPoint)
    return maskPoints, spotPoints, worldLines


def drawVehicle(vehicle, showMaskPoints, showSpotPoints, showGuides):
    geometry = getWorldGeometry(vehicle)
    if geometry is None:
        return
    maskPoints, spotPoints, lines = geometry
    maskPoints, spotPoints, lines = selectGeometry(
        maskPoints, spotPoints, lines, showMaskPoints, showSpotPoints,
        showGuides)
    drawer = DebugDrawer()
    for line in lines:
        drawLine(drawer, line)
    for point in maskPoints:
        drawSphere(drawer, point, 0.05, MASK_COLORS)
    for point in spotPoints:
        drawSphere(drawer, point, 0.05, SPOT_COLORS)
