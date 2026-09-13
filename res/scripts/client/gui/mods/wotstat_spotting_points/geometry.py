"""Local-space geometry, adapted from the hangar part of SpottingUtil.

Plain tuples keep these calculations independent of the native client modules.
The moving gun observation point is added by the renderer.
"""
from collections import namedtuple

LineGeometry = namedtuple('LineGeometry', 'points color backColor')


def addMovingGunPoint(maskPoints, spotPoints, point):
    resultMask = list(maskPoints)
    resultSpots = list(spotPoints)
    resultMask.append(point)
    resultSpots.append(point)
    return resultMask, resultSpots


def _pointsEqual(a, b):
    if hasattr(a, 'distSqrTo'):
        return a.distSqrTo(b) < 0.000001
    return sum((a[i] - b[i]) ** 2 for i in range(3)) < 0.000001


def selectGeometry(maskPoints, spotPoints, lines, showMaskPoints,
                   showSpotPoints, showGuides):
    selectedMask = list(maskPoints) if showMaskPoints else []
    selectedSpots = list(spotPoints) if showSpotPoints else []
    selectedLines = list(lines) if showGuides else []
    if selectedMask and selectedSpots:
        selectedMask = [point for point in selectedMask
                        if not any(_pointsEqual(point, spot)
                                   for spot in selectedSpots)]
    return selectedMask, selectedSpots, selectedLines


def bboxPoints(low, high):
    return [(low[0], low[1], low[2]), (low[0], high[1], low[2]),
            (low[0], high[1], high[2]), (low[0], low[1], high[2]),
            (high[0], low[1], low[2]), (high[0], high[1], low[2]),
            (high[0], high[1], high[2]), (high[0], low[1], high[2])]


def add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def buildGeometry(hullBounds, turretBounds, hullOffset, turretOffset, gunOffset):
    low = add(hullBounds[0], hullOffset)
    high = add(hullBounds[1], hullOffset)
    center = tuple((low[i] + high[i]) * 0.5 for i in range(3))
    turretOrigin = add(hullOffset, turretOffset)
    gun = add(turretOrigin, gunOffset)
    top = max(high[1], turretBounds[1][1] + turretOrigin[1])
    points = [
        (center[0], center[1], low[2]),
        (center[0], center[1], high[2]),
        (low[0], gun[1], center[2]),
        (high[0], gun[1], center[2]),
        gun,
        (0, top, 0),
    ]
    # Exact showBBoxes + showBBoxAlign polylines from SpottingUtil.
    hull = bboxPoints(low, high)
    upper = bboxPoints(low, (high[0], top, high[2]))
    lines = [LineGeometry([upper[i] for i in (2, 6, 5, 1, 2)], 0xffffff, None)]
    for indices in ((0, 1, 2, 3, 0, 4, 7, 3), (4, 5, 6, 7), (2, 6), (1, 5)):
        lines.append(LineGeometry([hull[i] for i in indices], 0xffffff, None))
    for indices in ((0, 2, 7, 5, 0), (4, 1, 3, 6, 4)):
        lines.append(LineGeometry([hull[i] for i in indices], 0x959595, None))
    lines.extend([
        LineGeometry([(low[0], center[1], center[2]), points[2],
                      (low[0], gun[1], gun[2])], 0x959595, None),
        LineGeometry([(low[0], gun[1], gun[2]),
                      (high[0], gun[1], gun[2])], 0x959595, 0x646464),
        LineGeometry([(high[0], gun[1], gun[2]), points[3],
                      (high[0], center[1], center[2])], 0x959595, None),
        LineGeometry([(center[0], top, center[2]), points[5], (0, 0, 0)], 0x959595, None),
        LineGeometry([upper[2], upper[5]], 0x959595, None),
        LineGeometry([upper[1], upper[6]], 0x959595, None),
    ])
    return points, lines
