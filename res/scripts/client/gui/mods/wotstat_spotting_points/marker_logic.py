# -*- coding: utf-8 -*-
from collections import namedtuple

MarkerData = namedtuple('MarkerData', 'id point label')

BODY_POINT_IDS = ('rear', 'front', 'left', 'right')
SPECIAL_POINT_IDS = ('gunStatic', 'top', 'gunMoving')

LABELS = {
    'rear': u'Задняя габаритная',
    'front': u'Передняя габаритная',
    'left': u'Левая бортовая габаритная',
    'right': u'Правая бортовая габаритная',
    'gunStatic': u'Исходная орудийная габаритная',
    'top': u'Верхняя обзорно-габаритная',
    'gunMoving': u'Орудийная обзорно-габаритная',
}


def isOverlaySceneActive(hasHangar, hasBlockingWindow):
    return bool(hasHangar and not hasBlockingWindow)


def _pointsEqual(a, b):
    if hasattr(a, 'distSqrTo'):
        return a.distSqrTo(b) < 0.000001
    return sum((a[i] - b[i]) ** 2 for i in range(3)) < 0.000001


def buildMarkerData(maskPoints, spotPoints):
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
        result.append(MarkerData(pointId, pointsById[pointId], LABELS[pointId]))
    return result


def buildOverlayData(markers):
    return [{'id': marker.id, 'label': marker.label, 'showLabel': True}
            for marker in markers]
