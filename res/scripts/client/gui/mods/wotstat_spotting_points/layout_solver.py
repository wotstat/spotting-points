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
RECONSIDER_DISTANCE_DELTA = 64.0
MAX_REPAIR_PASSES = 3
MAX_REPAIR_PAIR_SCORES = 192

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


def _buildSpanEdges(points):
    horizontal = []
    vertical = []
    for index, start in enumerate(points):
        end = points[(index + 1) % len(points)]
        deltaX = end[0] - start[0]
        deltaY = end[1] - start[1]
        if abs(deltaY) > EPSILON:
            slope = deltaX / deltaY
            horizontal.append((min(start[1], end[1]),
                               max(start[1], end[1]), slope,
                               start[0] - slope * start[1]))
        if abs(deltaX) > EPSILON:
            slope = deltaY / deltaX
            vertical.append((min(start[0], end[0]),
                             max(start[0], end[0]), slope,
                             start[1] - slope * start[0]))
    return horizontal, vertical


def _preparedSpan(points, edges, minimum, maximum, pointAxis,
                  valueAxis):
    minimumValue = None
    maximumValue = None
    for point in points:
        if minimum - EPSILON <= point[pointAxis] <= maximum + EPSILON:
            value = point[valueAxis]
            minimumValue = value if minimumValue is None else min(
                minimumValue, value)
            maximumValue = value if maximumValue is None else max(
                maximumValue, value)
    boundaries = ((minimum,) if abs(maximum - minimum) <= EPSILON
                  else (minimum, maximum))
    for boundary in boundaries:
        for edgeMinimum, edgeMaximum, slope, intercept in edges:
            if (edgeMinimum - EPSILON <= boundary
                    <= edgeMaximum + EPSILON):
                value = slope * boundary + intercept
                minimumValue = value if minimumValue is None else min(
                    minimumValue, value)
                maximumValue = value if maximumValue is None else max(
                    maximumValue, value)
    if minimumValue is None:
        return None
    return minimumValue, maximumValue


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


def polygonBounds(points):
    return (min(point[0] for point in points),
            min(point[1] for point in points),
            max(point[0] for point in points),
            max(point[1] for point in points))


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


def _subtractScores(first, second):
    return tuple(first[index] - second[index]
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
        self._lastChoiceByPointId = {}
        self._lastEvaluatedCostByPointId = {}
        self.lastChanged = False
        self.candidateCount = 0
        self.stablePlanHits = 0
        self.fullSearches = 0

    @property
    def revision(self):
        return self._revision

    def reset(self):
        self._revision = 0
        self._signature = None
        self._lastResult = None
        self._lastLaneByPointId.clear()
        self._lastChoiceByPointId.clear()
        self._lastEvaluatedCostByPointId.clear()
        self.lastChanged = False
        self.candidateCount = 0
        self.stablePlanHits = 0
        self.fullSearches = 0

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
        for pointId in tuple(self._lastChoiceByPointId):
            if pointId not in currentIds:
                del self._lastChoiceByPointId[pointId]
        for pointId in tuple(self._lastEvaluatedCostByPointId):
            if pointId not in currentIds:
                del self._lastEvaluatedCostByPointId[pointId]

        plan = self._stablePlan(
            orderedItems, geometry, float(width), float(height))
        if plan is None:
            plan = self._search(orderedItems, geometry, float(width),
                                float(height))
            evaluatedIds = currentIds
            self.fullSearches += 1
        else:
            evaluatedIds = plan.pop('_evaluatedIds', set())
            self.stablePlanHits += 1
        self._revision += 1
        self._signature = signature
        self.lastChanged = True
        for entry in plan['entries']:
            self._lastLaneByPointId[entry['id']] = entry['lane']
            self._lastChoiceByPointId[entry['id']] = (
                entry['lane'], entry['offsetIndex'])
            if entry['id'] in evaluatedIds:
                self._lastEvaluatedCostByPointId[entry['id']] = (
                    self._leaderCost(entry))
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

    def _stablePlan(self, items, geometry, width, height):
        currentIds = set(str(item['id']) for item in items)
        if not items or currentIds != set(self._lastChoiceByPointId):
            return None
        ordered = sorted(items, key=lambda item: (-float(item['width']),
                                                  str(item['id'])))
        entries = []
        score = (0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0.0)
        sideSpanCache = {}
        obstacles = (geometry['hull'], geometry['turret'])
        for item in ordered:
            lane, offsetIndex = self._lastChoiceByPointId[str(item['id'])]
            multiplier = _OFFSETS[offsetIndex]
            if lane == 'top':
                candidate = self._topCandidate(
                    item, multiplier, offsetIndex,
                    obstacles, width, height)
            else:
                candidate = self._sideCandidate(
                    item, lane, multiplier, offsetIndex,
                    obstacles, width, height, sideSpanCache)
            if candidate is None:
                return None
            entry = dict(candidate)
            entry['id'] = str(item['id'])
            entry['point'] = (float(item['x']), float(item['y']))
            entry['_localScore'] = self._candidateScore(
                item, entry, geometry, width, height)
            entry['_signature'] = self._candidateSignature(entry)
            score = _addScores(score, entry['_localScore'])
            for existing in entries:
                score = _addScores(
                    score, self._expandPairScore(
                        self._pairScore(existing, entry)))
            entries.append(entry)
        self.candidateCount = len(entries)
        previousScore = self._lastResult['score']
        worsened = self._stableScoreWorsened(score, previousScore)
        reconsiderIds = set()
        if worsened:
            reconsiderIds.update(self._conflictingIds(entries))
            if score[0]:
                reconsiderIds.update(
                    entry['id'] for entry in entries
                    if entry['_localScore'][0])
            if score[7]:
                reconsiderIds.update(
                    entry['id'] for entry in entries
                    if entry['_localScore'][7])
        if not reconsiderIds:
            reconsiderIds.update(
                entry['id'] for entry in entries
                if self._leaderCost(entry)
                > self._lastEvaluatedCostByPointId.get(
                    entry['id'], self._leaderCost(entry))
                + RECONSIDER_DISTANCE_DELTA)
        if reconsiderIds:
            candidateSets = {}
            itemById = dict((str(item['id']), item) for item in items)
            for pointId in sorted(reconsiderIds):
                item = itemById[pointId]
                candidates = self._buildCandidates(
                    item, geometry, width, height)
                self.candidateCount += len(candidates)
                prepared = []
                for candidate in candidates:
                    entry = dict(candidate)
                    entry['id'] = pointId
                    entry['point'] = (float(item['x']), float(item['y']))
                    entry['_localScore'] = self._candidateScore(
                        item, entry, geometry, width, height)
                    entry['_signature'] = self._candidateSignature(entry)
                    prepared.append(entry)
                prepared.sort(key=lambda entry: (entry['_localScore'],
                                                 entry['_signature']))
                candidateSets[pointId] = prepared
            plan = self._repairPlan(
                {'score': score,
                 'signature': ''.join(entry['_signature']
                                    for entry in entries),
                 'entries': entries},
                candidateSets, reconsiderIds)
            score = plan['score']
            entries = plan['entries']
            worsened = self._stableScoreWorsened(score, previousScore)
        if worsened:
            return None
        return {'score': score,
                'signature': ''.join(entry['_signature']
                                   for entry in entries),
                'entries': entries,
                '_evaluatedIds': reconsiderIds}

    def _stableScoreWorsened(self, score, previousScore):
        for countIndex in (0, 2, 4, 6, 7):
            if score[countIndex] != previousScore[countIndex]:
                return score[countIndex] > previousScore[countIndex]
        return False

    def _search(self, items, geometry, width, height):
        ordered = sorted(items, key=lambda item: (-float(item['width']),
                                                  str(item['id'])))
        zeroScore = (0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0.0)
        selected = []
        score = zeroScore
        candidateSets = {}
        self.candidateCount = 0
        for item in ordered:
            candidates = self._buildCandidates(
                item, geometry, width, height)
            self.candidateCount += len(candidates)
            prepared = []
            for candidate in candidates:
                entry = dict(candidate)
                entry['id'] = str(item['id'])
                entry['point'] = (float(item['x']), float(item['y']))
                entry['_localScore'] = self._candidateScore(
                    item, entry, geometry, width, height)
                entry['_signature'] = self._candidateSignature(entry)
                prepared.append(entry)
            prepared.sort(key=lambda entry: (entry['_localScore'],
                                             entry['_signature']))
            candidateSets[str(item['id'])] = prepared
            bestEntry, bestScore = self._bestCandidate(
                prepared, selected, score)
            selected.append(bestEntry)
            score = bestScore
        plan = {'score': score,
                'signature': ''.join(entry['_signature']
                                   for entry in selected),
                'entries': selected}
        if any(score[index] for index in (2, 4, 6)):
            plan = self._repairPlan(plan, candidateSets)
        return plan

    def _bestCandidate(self, candidates, selected, baseScore):
        bestEntry = None
        bestScore = None
        for entry in candidates:
            pairScore = (0, 0.0, 0, 0.0, 0)
            for existing in selected:
                pairScore = _addScores(
                    pairScore, self._pairScore(existing, entry))
            score = _addScores(
                baseScore, _addScores(
                    entry['_localScore'],
                    self._expandPairScore(pairScore)))
            if (bestScore is None or score < bestScore
                    or (score == bestScore
                        and entry['_signature'] < bestEntry['_signature'])):
                bestEntry = entry
                bestScore = score
            if not any(pairScore[index] for index in (0, 2, 4)):
                break
        return bestEntry, bestScore

    def _repairPlan(self, plan, candidateSets, reconsiderIds=None):
        entries = list(plan['entries'])
        score = plan['score']
        evaluations = 0
        reconsiderIds = set(reconsiderIds or ())
        for unusedPass in xrange(MAX_REPAIR_PASSES):
            conflicts = self._conflictingIds(entries)
            conflicts.update(reconsiderIds)
            reconsiderIds.clear()
            if not conflicts:
                break
            improved = False
            for index, current in enumerate(tuple(entries)):
                if current['id'] not in conflicts:
                    continue
                candidates = candidateSets.get(current['id'])
                if candidates is None:
                    continue
                others = entries[:index] + entries[index + 1:]
                if evaluations + len(others) > MAX_REPAIR_PAIR_SCORES:
                    break
                removed = current['_localScore']
                for other in others:
                    removed = _addScores(
                        removed, self._expandPairScore(
                            self._pairScore(current, other)))
                    evaluations += 1
                baseScore = _subtractScores(score, removed)
                bestEntry = current
                bestScore = score
                for candidate in candidates:
                    if evaluations + len(others) > MAX_REPAIR_PAIR_SCORES:
                        break
                    pairScore = (0, 0.0, 0, 0.0, 0)
                    for other in others:
                        pairScore = _addScores(
                            pairScore, self._pairScore(candidate, other))
                        evaluations += 1
                    candidateScore = _addScores(
                        baseScore, _addScores(
                            candidate['_localScore'],
                            self._expandPairScore(pairScore)))
                    if (candidateScore < bestScore
                            or (candidateScore == bestScore
                                and candidate['_signature']
                                < bestEntry['_signature'])):
                        bestEntry = candidate
                        bestScore = candidateScore
                    if (not any(pairScore[position]
                               for position in (0, 2, 4))):
                        break
                if bestEntry is not current:
                    entries[index] = bestEntry
                    score = bestScore
                    improved = True
                if evaluations + len(others) > MAX_REPAIR_PAIR_SCORES:
                    break
            if not improved or evaluations >= MAX_REPAIR_PAIR_SCORES:
                break
        return {'score': score,
                'signature': ''.join(entry['_signature']
                                   for entry in entries),
                'entries': entries}

    def _conflictingIds(self, entries):
        conflicts = set()
        for index, first in enumerate(entries):
            for second in entries[index + 1:]:
                score = self._pairScore(first, second)
                if any(score[position] for position in (0, 2, 4)):
                    conflicts.add(first['id'])
                    conflicts.add(second['id'])
        return conflicts

    def _candidateScore(self, item, candidate, geometry, width, height):
        rectangle = candidate['rect']
        safeRectangle = (SCREEN_MARGIN, SCREEN_MARGIN,
                         max(0.0, width - SCREEN_MARGIN * 2.0),
                         max(0.0, height - SCREEN_MARGIN * 2.0))
        rectangleArea = max(0.0, rectangle[2]) * max(0.0, rectangle[3])
        overflowArea = max(
            0.0, rectangleArea
            - rectangleIntersectionArea(rectangle, safeRectangle))
        if overflowArea <= EPSILON:
            overflowArea = 0.0
        overflowCount = 1 if overflowArea else 0
        forbiddenCount = 0
        forbiddenArea = 0.0
        for part in ('hull', 'turret'):
            bounds = geometry[part]['bounds']
            boundsRectangle = (bounds[0], bounds[1],
                               bounds[2] - bounds[0],
                               bounds[3] - bounds[1])
            if rectangleIntersectionArea(
                    rectangle, boundsRectangle) <= EPSILON:
                continue
            area = rectanglePolygonIntersectionArea(
                rectangle, geometry[part]['obstacle'])
            if area > EPSILON:
                forbiddenCount += 1
                forbiddenArea += area
        return (overflowCount, overflowArea, 0, 0.0, 0, 0.0, 0,
                forbiddenCount, forbiddenArea,
                self._ordinaryCost(item, candidate))

    def _ordinaryCost(self, item, candidate):
        length = self._leaderCost(candidate)
        remembered = self._lastLaneByPointId.get(str(item['id']))
        if remembered is not None and remembered != candidate['lane']:
            length += LANE_SWITCH_PENALTY
        return length

    def _leaderCost(self, candidate):
        length = _polylineLength(candidate['leader'])
        if candidate['lane'] == 'top':
            length *= TOP_LEADER_WEIGHT
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
        if overlapArea <= EPSILON:
            overlapArea = 0.0
        overlapCount = 1 if overlapArea else 0
        crossingCount = 1 if _polylinesIntersect(
            first['leader'], second['leader']) else 0
        return (pointCount, pointPenetration,
                overlapCount, overlapArea, crossingCount)

    def _expandPairScore(self, pairScore):
        return (0, 0.0, pairScore[0], pairScore[1],
                pairScore[2], pairScore[3], pairScore[4],
                0, 0.0, 0.0)

    def _candidateSignature(self, candidate):
        return '|%s:%d' % (candidate['lane'], candidate['offsetIndex'])

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
        obstacle = inflateConvexPolygon(outline, BOUNDS_PADDING)
        horizontalEdges, verticalEdges = _buildSpanEdges(obstacle)
        return {
            'points': projected,
            'outline': outline,
            'obstacle': obstacle,
            'bounds': polygonBounds(obstacle),
            'horizontalEdges': horizontalEdges,
            'verticalEdges': verticalEdges
        }

    def _buildCandidates(self, item, geometry, width, height):
        obstacles = (geometry['hull'], geometry['turret'])
        candidates = []
        sideSpanCache = {}
        for lane in ('left', 'right'):
            for offsetIndex, multiplier in enumerate(_OFFSETS):
                candidate = self._sideCandidate(
                    item, lane, multiplier, offsetIndex,
                    obstacles, width, height, sideSpanCache)
                if candidate is not None:
                    candidates.append(candidate)
        for offsetIndex, multiplier in enumerate(_OFFSETS):
            candidates.append(self._topCandidate(
                item, multiplier, offsetIndex, obstacles, width, height))
        deduplicated = []
        seen = set()
        for candidate in candidates:
            rectangle = candidate['rect']
            key = (candidate['lane'],) + rectangle
            if key in seen:
                continue
            seen.add(key)
            candidate['candidateIndex'] = len(deduplicated)
            deduplicated.append(candidate)
        return deduplicated

    def _sideCandidate(self, item, lane, multiplier, offsetIndex,
                       obstacles, width, height, spanCache):
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
        spanKey = (boxY, calloutHeight)
        spans = spanCache.get(spanKey)
        if spans is None:
            spans = [self._horizontalSpan(
                obstacle, boxY, boxY + calloutHeight)
                for obstacle in obstacles]
            spans = [span for span in spans if span is not None]
            spanCache[spanKey] = spans
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
        spans = [self._verticalSpan(obstacle, boxX, boxX + calloutWidth)
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

    def _horizontalSpan(self, part, minimumY, maximumY):
        bounds = part['bounds']
        if maximumY < bounds[1] or minimumY > bounds[3]:
            return None
        return _preparedSpan(
            part['obstacle'], part['horizontalEdges'],
            minimumY, maximumY, 1, 0)

    def _verticalSpan(self, part, minimumX, maximumX):
        bounds = part['bounds']
        if maximumX < bounds[0] or minimumX > bounds[2]:
            return None
        return _preparedSpan(
            part['obstacle'], part['verticalEdges'],
            minimumX, maximumX, 0, 1)
