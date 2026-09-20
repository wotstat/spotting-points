# -*- coding: utf-8 -*-
from collections import namedtuple

from .localization import getMarkerLabels

MarkerData = namedtuple('MarkerData', 'id point label')

BODY_POINT_IDS = ('rear', 'front', 'left', 'right')
SPECIAL_POINT_IDS = ('gunStatic', 'top', 'gunMoving')


def isOverlaySceneActive(hasVehicleScene, hasBlockingWindow):
    return bool(hasVehicleScene and not hasBlockingWindow)


def _pointsEqual(a, b):
    if hasattr(a, 'distSqrTo'):
        return a.distSqrTo(b) < 0.000001
    return sum((a[i] - b[i]) ** 2 for i in range(3)) < 0.000001


def buildMarkerData(maskPoints, spotPoints, language=None):
    labels = getMarkerLabels(language)
    pointsById = {
        'rear': maskPoints[0],
        'front': maskPoints[1],
        'left': maskPoints[2],
        'right': maskPoints[3],
        'gunStatic': maskPoints[4],
        'top': spotPoints[0],
        'gunMoving': spotPoints[1],
    }
    result = []
    for pointId in BODY_POINT_IDS + SPECIAL_POINT_IDS:
        if (pointId == 'gunStatic'
                and _pointsEqual(pointsById[pointId], pointsById['gunMoving'])):
            continue
        result.append(MarkerData(pointId, pointsById[pointId], labels[pointId]))
    return result


def buildOverlayData(markers):
    return [{'id': marker.id, 'label': marker.label, 'showLabel': True}
            for marker in markers]
