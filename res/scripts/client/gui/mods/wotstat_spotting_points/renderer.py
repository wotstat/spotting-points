from DebugDrawer import DebugDrawer
from Math import Matrix, Vector3
from realm import CURRENT_REALM
from vehicle_systems.tankStructure import TankPartIndexes, TankNodeNames

from .geometry import (
  addMovingGunPoint, buildGeometry, buildHighlightGroups, buildLayoutBounds,
  buildTurretArc, buildTurretCircle, LineGeometry, selectGeometry)

MASK_COLORS = (0xff3135, 0xab6d67)
SPOT_COLORS = (0x00aaff, 0x5990bf)
# The clients submit DebugDrawer primitives in opposite order.
PASSES = (False, True) if CURRENT_REALM == 'RU' else (True, False)


def getLayoutBounds(vehicle):
  collisions = vehicle.appearance.collisions

  if collisions is None:
    return None

  hullBounds = collisions.getBoundingBox(TankPartIndexes.HULL)
  turretBounds = collisions.getBoundingBox(TankPartIndexes.TURRET)

  if not hullBounds or not turretBounds:
    return None

  return buildLayoutBounds(hullBounds, turretBounds)


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


def getWorldGeometry(vehicle, includeLines=True, includeGunCircle=False):
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
  worldLines = None

  if includeLines:
    worldLines = [LineGeometry(
      [matrix.applyPoint(Vector3(p)) for p in line.points],
      line.color, line.backColor) for line in lines]

  # This model node already includes actual turret rotation, yaw limits,
  # static angles and customization animations in both clients.
  gunJoint = vehicle.model.node(TankNodeNames.GUN_JOINT)

  if gunJoint is None:
    return None

  movingPoint = Vector3(gunJoint.position)
  movingArc = None
  gunCircle = None

  if includeLines:
    inverseMatrix = Matrix(matrix)
    inverseMatrix.invert()
    movingPointLocal = inverseMatrix.applyPoint(movingPoint)
    turretAxis = tuple(hullOffset[i] + turretOffset[i] for i in range(3))
    arcPoints = buildTurretArc(turretAxis, points[4], movingPointLocal)

    if arcPoints:
      worldArc = [matrix.applyPoint(Vector3(p)) for p in arcPoints]
      worldArc[0] = maskPoints[4]
      worldArc[-1] = movingPoint
      movingArc = LineGeometry(worldArc, 0x959595, 0x646464)
      worldLines.append(movingArc)

    if includeGunCircle:
      circlePoints = buildTurretCircle(turretAxis, points[4])

      if circlePoints:
        worldCircle = [matrix.applyPoint(Vector3(p))
              for p in circlePoints]
        worldCircle[0] = maskPoints[4]
        worldCircle[-1] = maskPoints[4]
        gunCircle = LineGeometry(worldCircle, 0x959595, None)

  maskPoints, spotPoints = addMovingGunPoint(
    maskPoints, [maskPoints[5]], movingPoint)
  highlights = (buildHighlightGroups(worldLines, movingArc, gunCircle)
        if includeLines else {})

  return maskPoints, spotPoints, worldLines, highlights


def drawGeometry(geometry, showMaskPoints, showSpotPoints, showGuides,
        hoveredPointId=None):
  maskPoints, spotPoints, lines, highlights = geometry
  selectedMask, selectedSpots, selectedLines = selectGeometry(
    maskPoints, spotPoints, lines or (), showMaskPoints, showSpotPoints,
    showGuides)

  if not (selectedMask or selectedSpots or selectedLines):
    return

  drawer = DebugDrawer()

  for line in selectedLines:
    drawLine(drawer, line)

  for point in selectedMask:
    drawSphere(drawer, point, 0.05, MASK_COLORS)

  for point in selectedSpots:
    drawSphere(drawer, point, 0.05, SPOT_COLORS)


def drawVehicle(vehicle, showMaskPoints, showSpotPoints, showGuides,
        hoveredPointId=None):
  geometry = getWorldGeometry(
    vehicle, showGuides or hoveredPointId is not None,
    hoveredPointId == 'gunMoving')

  if geometry is None:
    return None

  drawGeometry(geometry, showMaskPoints, showSpotPoints, showGuides,
        hoveredPointId)

  return geometry
