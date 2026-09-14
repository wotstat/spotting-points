import math


EPSILON = 0.0001
BOUNDS_PADDING = 18.0
CALLOUT_GAP = 28.0
EDGE_OFFSET = 18.0
SCREEN_MARGIN = 8.0
TOP_HORIZONTAL_GAP = 12.0
POINT_CLEARANCE_RADIUS = 10.0
TOP_LEADER_WEIGHT = 1.15
LANE_SWITCH_PENALTY = 180.0
BEAM_WIDTH = 64

_INFLATE_SIDES = 8
_INFLATE_RADIUS_SCALE = 1.082392200292394
_OFFSETS = (0, -1, 1, -2, 2)


def _cross(origin, first, second):
    return ((first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0]))


def convexHull(inputPoints):
    points = sorted((float(point[0]), float(point[1]))
                    for point in inputPoints)
    unique = []
    for point in points:
        if (not unique or abs(unique[-1][0] - point[0]) > EPSILON
                or abs(unique[-1][1] - point[1]) > EPSILON):
            unique.append(point)
    if len(unique) <= 2:
        return unique
    lower = []
    for point in unique:
        while (len(lower) >= 2
               and _cross(lower[-2], lower[-1], point) <= EPSILON):
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(unique):
        while (len(upper) >= 2
               and _cross(upper[-2], upper[-1], point) <= EPSILON):
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def inflateConvexPolygon(points, padding):
    if not points or padding <= 0.0:
        return list(points or ())
    cloud = []
    radius = padding * _INFLATE_RADIUS_SCALE
    for point in points:
        for index in xrange(_INFLATE_SIDES):
            angle = math.pi * 2.0 * index / _INFLATE_SIDES
            cloud.append((point[0] + math.cos(angle) * radius,
                          point[1] + math.sin(angle) * radius))
    return convexHull(cloud)


def _range(values):
    return (min(values), max(values)) if values else None


def horizontalSpan(points, minimumY, maximumY):
    if len(points) < 3:
        return None
    values = [point[0] for point in points
              if minimumY - EPSILON <= point[1] <= maximumY + EPSILON]
    for y in ((minimumY,) if abs(maximumY - minimumY) <= EPSILON
              else (minimumY, maximumY)):
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            if (y < min(start[1], end[1]) - EPSILON
                    or y > max(start[1], end[1]) + EPSILON
                    or abs(end[1] - start[1]) <= EPSILON):
                continue
            ratio = (y - start[1]) / (end[1] - start[1])
            values.append(start[0] + (end[0] - start[0]) * ratio)
    return _range(values)


def verticalSpan(points, minimumX, maximumX):
    if len(points) < 3:
        return None
    values = [point[1] for point in points
              if minimumX - EPSILON <= point[0] <= maximumX + EPSILON]
    for x in ((minimumX,) if abs(maximumX - minimumX) <= EPSILON
              else (minimumX, maximumX)):
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            if (x < min(start[0], end[0]) - EPSILON
                    or x > max(start[0], end[0]) + EPSILON
                    or abs(end[0] - start[0]) <= EPSILON):
                continue
            ratio = (x - start[0]) / (end[0] - start[0])
            values.append(start[1] + (end[1] - start[1]) * ratio)
    return _range(values)


def _clipPolygon(points, inside, intersection):
    if not points:
        return []
    output = []
    previous = points[-1]
    previousInside = inside(previous)
    for current in points:
        currentInside = inside(current)
        if currentInside:
            if not previousInside:
                output.append(intersection(previous, current))
            output.append(current)
        elif previousInside:
            output.append(intersection(previous, current))
        previous = current
        previousInside = currentInside
    return output


def _clipVertical(points, bound, keepGreater):
    def inside(point):
        return (point[0] >= bound - EPSILON if keepGreater
                else point[0] <= bound + EPSILON)

    def intersection(start, end):
        delta = end[0] - start[0]
        if abs(delta) <= EPSILON:
            return (bound, start[1])
        ratio = (bound - start[0]) / delta
        return (bound, start[1] + (end[1] - start[1]) * ratio)
    return _clipPolygon(points, inside, intersection)


def _clipHorizontal(points, bound, keepGreater):
    def inside(point):
        return (point[1] >= bound - EPSILON if keepGreater
                else point[1] <= bound + EPSILON)

    def intersection(start, end):
        delta = end[1] - start[1]
        if abs(delta) <= EPSILON:
            return (start[0], bound)
        ratio = (bound - start[1]) / delta
        return (start[0] + (end[0] - start[0]) * ratio, bound)
    return _clipPolygon(points, inside, intersection)


def polygonArea(points):
    if len(points) < 3:
        return 0.0
    total = 0.0
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        total += point[0] * following[1] - point[1] * following[0]
    return abs(total) * 0.5


def rectanglePolygonIntersectionArea(rectangle, polygon):
    x, y, width, height = rectangle
    clipped = list(polygon)
    clipped = _clipVertical(clipped, x, True)
    clipped = _clipVertical(clipped, x + width, False)
    clipped = _clipHorizontal(clipped, y, True)
    clipped = _clipHorizontal(clipped, y + height, False)
    return polygonArea(clipped)


def rectangleIntersectionArea(first, second):
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[0] + first[2], second[0] + second[2])
    bottom = min(first[1] + first[3], second[1] + second[3])
    return max(0.0, right - left) * max(0.0, bottom - top)


def _pointOnSegment(point, start, end):
    return (abs(_cross(start, end, point)) <= EPSILON
            and min(start[0], end[0]) - EPSILON <= point[0]
            <= max(start[0], end[0]) + EPSILON
            and min(start[1], end[1]) - EPSILON <= point[1]
            <= max(start[1], end[1]) + EPSILON)


def segmentsIntersect(firstStart, firstEnd, secondStart, secondEnd):
    firstSecondStart = _cross(firstStart, firstEnd, secondStart)
    firstSecondEnd = _cross(firstStart, firstEnd, secondEnd)
    secondFirstStart = _cross(secondStart, secondEnd, firstStart)
    secondFirstEnd = _cross(secondStart, secondEnd, firstEnd)
    if (((firstSecondStart > EPSILON and firstSecondEnd < -EPSILON)
         or (firstSecondStart < -EPSILON and firstSecondEnd > EPSILON))
            and ((secondFirstStart > EPSILON
                  and secondFirstEnd < -EPSILON)
                 or (secondFirstStart < -EPSILON
                     and secondFirstEnd > EPSILON))):
        return True
    return (abs(firstSecondStart) <= EPSILON
            and _pointOnSegment(secondStart, firstStart, firstEnd)
            or abs(firstSecondEnd) <= EPSILON
            and _pointOnSegment(secondEnd, firstStart, firstEnd)
            or abs(secondFirstStart) <= EPSILON
            and _pointOnSegment(firstStart, secondStart, secondEnd)
            or abs(secondFirstEnd) <= EPSILON
            and _pointOnSegment(firstEnd, secondStart, secondEnd))


def pointSegmentDistance(point, start, end):
    deltaX = end[0] - start[0]
    deltaY = end[1] - start[1]
    lengthSquared = deltaX * deltaX + deltaY * deltaY
    if lengthSquared <= EPSILON:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    ratio = ((point[0] - start[0]) * deltaX
             + (point[1] - start[1]) * deltaY) / lengthSquared
    ratio = _clamp(ratio, 0.0, 1.0)
    nearest = (start[0] + ratio * deltaX, start[1] + ratio * deltaY)
    return math.hypot(point[0] - nearest[0], point[1] - nearest[1])


def _polylineLength(points):
    return sum(math.hypot(end[0] - start[0], end[1] - start[1])
               for start, end in zip(points, points[1:]))


def _pointPolylineDistance(point, polyline):
    return min(pointSegmentDistance(point, start, end)
               for start, end in zip(polyline, polyline[1:]))


def _polylinesIntersect(first, second):
    for firstStart, firstEnd in zip(first, first[1:]):
        if (abs(firstEnd[0] - firstStart[0]) <= EPSILON
                and abs(firstEnd[1] - firstStart[1]) <= EPSILON):
            continue
        for secondStart, secondEnd in zip(second, second[1:]):
            if (abs(secondEnd[0] - secondStart[0]) <= EPSILON
                    and abs(secondEnd[1] - secondStart[1]) <= EPSILON):
                continue
            if segmentsIntersect(firstStart, firstEnd,
                                 secondStart, secondEnd):
                return True
    return False


def _addScores(first, second):
    return tuple(first[index] + second[index]
                 for index in xrange(len(first)))


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _quantize(value):
    return int(round(float(value) * 4.0))


def _pointList(points):
    return [(float(point[0]), float(point[1])) for point in points]


class CalloutLayoutSolver(object):
    def __init__(self):
        self._revision = 0
        self._signature = None
        self._lastResult = None
        self._lastLaneByPointId = {}
        self.lastChanged = False
        self.candidateCount = 0

    def reset(self):
        self._revision = 0
        self._signature = None
        self._lastResult = None
        self._lastLaneByPointId.clear()
        self.lastChanged = False
        self.candidateCount = 0

    def solve(self, width, height, hullPoints, turretPoints, items):
        orderedItems = sorted(items, key=lambda item: str(item['id']))
        signature = self._inputSignature(
            width, height, hullPoints, turretPoints, orderedItems)
        if signature == self._signature:
            self.lastChanged = False
            return {'revision': self._revision}

        geometry = self._buildGeometry(hullPoints, turretPoints)
        currentIds = set(str(item['id']) for item in orderedItems)
        for pointId in tuple(self._lastLaneByPointId):
            if pointId not in currentIds:
                del self._lastLaneByPointId[pointId]

        plan = self._search(orderedItems, geometry, float(width),
                            float(height))
        self._revision += 1
        self._signature = signature
        self.lastChanged = True
        for entry in plan['entries']:
            self._lastLaneByPointId[entry['id']] = entry['lane']
        result = self._serializeResult(geometry, plan)
        self._lastResult = result
        return result

    def _inputSignature(self, width, height, hullPoints,
                        turretPoints, items):
        values = [_quantize(width), _quantize(height)]
        for points in (hullPoints, turretPoints):
            values.append(len(points))
            for point in points:
                values.extend((_quantize(point[0]), _quantize(point[1])))
        for item in items:
            values.extend((str(item['id']), str(item['part']),
                           _quantize(item['x']), _quantize(item['y']),
                           _quantize(item['width']),
                           _quantize(item['height'])))
        return tuple(values)

    def _search(self, items, geometry, width, height):
        ordered = sorted(items, key=lambda item: (-float(item['width']),
                                                  str(item['id'])))
        plans = [{'score': (0, 0.0, 0, 0.0, 0, 0.0,
                            0, 0, 0.0, 0.0),
                  'signature': '', 'entries': []}]
        self.candidateCount = 0
        for item in ordered:
            candidates = self._buildCandidates(
                item, geometry, width, height)
            self.candidateCount += len(candidates)
            expanded = []
            for candidate in candidates:
                entry = dict(candidate)
                entry['id'] = str(item['id'])
                entry['point'] = (float(item['x']), float(item['y']))
                localScore = self._candidateScore(
                    item, entry, geometry, width, height)
                signaturePart = self._candidateSignature(entry)
                for plan in plans:
                    score = _addScores(plan['score'], localScore)
                    for existing in plan['entries']:
                        score = _addScores(
                            score, self._expandPairScore(
                                self._pairScore(existing, entry)))
                    expanded.append({
                        'score': score,
                        'signature': plan['signature'] + signaturePart,
                        'entries': plan['entries'] + [entry]
                    })
            expanded.sort(key=lambda plan: (plan['score'],
                                            plan['signature']))
            plans = expanded[:BEAM_WIDTH]
        return plans[0] if plans else {
            'score': (0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0.0),
            'signature': '', 'entries': []}

    def _candidateScore(self, item, candidate, geometry, width, height):
        rectangle = candidate['rect']
        safeRectangle = (SCREEN_MARGIN, SCREEN_MARGIN,
                         max(0.0, width - SCREEN_MARGIN * 2.0),
                         max(0.0, height - SCREEN_MARGIN * 2.0))
        rectangleArea = max(0.0, rectangle[2]) * max(0.0, rectangle[3])
        overflowArea = max(
            0.0, rectangleArea
            - rectangleIntersectionArea(rectangle, safeRectangle))
        overflowCount = 1 if overflowArea > EPSILON else 0
        forbiddenCount = 0
        forbiddenArea = 0.0
        for part in ('hull', 'turret'):
            area = rectanglePolygonIntersectionArea(
                rectangle, geometry[part]['obstacle'])
            if area > EPSILON:
                forbiddenCount += 1
                forbiddenArea += area
        return (overflowCount, overflowArea, 0, 0.0, 0, 0.0, 0,
                forbiddenCount, forbiddenArea,
                self._ordinaryCost(item, candidate))

    def _ordinaryCost(self, item, candidate):
        length = _polylineLength(candidate['leader'])
        if candidate['lane'] == 'top':
            length *= TOP_LEADER_WEIGHT
        remembered = self._lastLaneByPointId.get(str(item['id']))
        if remembered is not None and remembered != candidate['lane']:
            length += LANE_SWITCH_PENALTY
        return length

    def _pairScore(self, first, second):
        firstPointDistance = _pointPolylineDistance(
            first['point'], second['leader'])
        secondPointDistance = _pointPolylineDistance(
            second['point'], first['leader'])
        pointDistances = (firstPointDistance, secondPointDistance)
        pointCount = sum(distance < POINT_CLEARANCE_RADIUS - EPSILON
                         for distance in pointDistances)
        pointPenetration = sum(
            POINT_CLEARANCE_RADIUS - distance for distance in pointDistances
            if distance < POINT_CLEARANCE_RADIUS - EPSILON)
        overlapArea = rectangleIntersectionArea(first['rect'],
                                                second['rect'])
        overlapCount = 1 if overlapArea > EPSILON else 0
        crossingCount = 1 if _polylinesIntersect(
            first['leader'], second['leader']) else 0
        return (pointCount, pointPenetration,
                overlapCount, overlapArea, crossingCount)

    def _expandPairScore(self, pairScore):
        return (0, 0.0, pairScore[0], pairScore[1],
                pairScore[2], pairScore[3], pairScore[4],
                0, 0.0, 0.0)

    def _candidateSignature(self, candidate):
        return '|%s:%d:%s' % (
            candidate['lane'], candidate['offsetIndex'],
            ','.join(str(_quantize(value))
                     for value in candidate['rect']))

    def _serializeResult(self, geometry, plan):
        placements = []
        for entry in sorted(plan['entries'], key=lambda value: value['id']):
            placements.append({
                'id': entry['id'],
                'lane': entry['lane'],
                'rect': list(entry['rect']),
                'leader': [list(point) for point in entry['leader']]
            })
        return {
            'revision': self._revision,
            'hull': self._serializePart(geometry['hull']),
            'turret': self._serializePart(geometry['turret']),
            'placements': placements,
            'score': list(plan['score'])
        }

    def _serializePart(self, part):
        return {
            'points': [list(point) for point in part['points']],
            'outline': [list(point) for point in part['outline']],
            'obstacle': [list(point) for point in part['obstacle']]
        }

    def _buildGeometry(self, hullPoints, turretPoints):
        return {
            'hull': self._buildPart(hullPoints),
            'turret': self._buildPart(turretPoints)
        }

    def _buildPart(self, points):
        projected = _pointList(points)
        outline = convexHull(projected)
        return {
            'points': projected,
            'outline': outline,
            'obstacle': inflateConvexPolygon(outline, BOUNDS_PADDING)
        }

    def _buildCandidates(self, item, geometry, width, height):
        obstacles = (geometry['hull']['obstacle'],
                     geometry['turret']['obstacle'])
        candidates = []
        for lane in ('left', 'right'):
            for offsetIndex, multiplier in enumerate(_OFFSETS):
                candidate = self._sideCandidate(
                    item, lane, multiplier, offsetIndex,
                    obstacles, width, height)
                if candidate is not None:
                    candidates.append(candidate)
        for offsetIndex, multiplier in enumerate(_OFFSETS):
            candidates.append(self._topCandidate(
                item, multiplier, offsetIndex, obstacles, width, height))
        deduplicated = []
        seen = set()
        for candidate in candidates:
            rectangle = candidate['rect']
            key = ((candidate['lane'],) +
                   tuple(_quantize(value) for value in rectangle))
            if key in seen:
                continue
            seen.add(key)
            candidate['candidateIndex'] = len(deduplicated)
            deduplicated.append(candidate)
        return deduplicated

    def _sideCandidate(self, item, lane, multiplier, offsetIndex,
                       obstacles, width, height):
        markerX = float(item['x'])
        markerY = float(item['y'])
        calloutWidth = float(item['width'])
        calloutHeight = float(item['height'])
        halfHeight = calloutHeight * 0.5
        centerY = _clamp(
            markerY + multiplier * CALLOUT_GAP,
            SCREEN_MARGIN + halfHeight,
            max(SCREEN_MARGIN + halfHeight,
                height - SCREEN_MARGIN - halfHeight))
        boxY = centerY - halfHeight
        spans = [horizontalSpan(obstacle, boxY, boxY + calloutHeight)
                 for obstacle in obstacles]
        spans = [span for span in spans if span is not None]
        if lane == 'left':
            baseEdge = (min(span[0] for span in spans) - EDGE_OFFSET
                        if spans else markerX - EDGE_OFFSET)
            desiredEdge = min(baseEdge,
                              markerX - abs(centerY - markerY))
            boxX = desiredEdge - calloutWidth
        else:
            baseEdge = (max(span[1] for span in spans) + EDGE_OFFSET
                        if spans else markerX + EDGE_OFFSET)
            desiredEdge = max(baseEdge,
                              markerX + abs(centerY - markerY))
            boxX = desiredEdge
        boxX = _clamp(
            boxX, SCREEN_MARGIN,
            max(SCREEN_MARGIN,
                width - SCREEN_MARGIN - calloutWidth))
        edgeX = boxX + calloutWidth if lane == 'left' else boxX
        reach = abs(edgeX - markerX)
        minimumTargetY = max(boxY, markerY - reach)
        maximumTargetY = min(boxY + calloutHeight, markerY + reach)
        if minimumTargetY > maximumTargetY + EPSILON:
            return None
        targetY = _clamp(centerY, minimumTargetY, maximumTargetY)
        direction = -1.0 if lane == 'left' else 1.0
        elbow = (markerX + direction * abs(targetY - markerY), targetY)
        rectangle = (boxX, boxY, calloutWidth, calloutHeight)
        return {
            'lane': lane,
            'offsetIndex': offsetIndex,
            'rect': rectangle,
            'leader': [(markerX, markerY), elbow, (edgeX, targetY)]
        }

    def _topCandidate(self, item, multiplier, offsetIndex,
                      obstacles, width, height):
        markerX = float(item['x'])
        markerY = float(item['y'])
        calloutWidth = float(item['width'])
        calloutHeight = float(item['height'])
        step = calloutWidth + TOP_HORIZONTAL_GAP
        boxX = markerX - calloutWidth * 0.5 + multiplier * step
        boxX = _clamp(
            boxX, SCREEN_MARGIN,
            max(SCREEN_MARGIN,
                width - SCREEN_MARGIN - calloutWidth))
        spans = [verticalSpan(obstacle, boxX, boxX + calloutWidth)
                 for obstacle in obstacles]
        spans = [span for span in spans if span is not None]
        topEdge = min(span[0] for span in spans) if spans else markerY
        boxY = _clamp(
            topEdge - EDGE_OFFSET - calloutHeight,
            SCREEN_MARGIN,
            max(SCREEN_MARGIN,
                height - SCREEN_MARGIN - calloutHeight))
        targetX = _clamp(markerX, boxX, boxX + calloutWidth)
        rectangle = (boxX, boxY, calloutWidth, calloutHeight)
        return {
            'lane': 'top',
            'offsetIndex': offsetIndex,
            'rect': rectangle,
            'leader': [(markerX, markerY),
                       (targetX, boxY + calloutHeight)]
        }
