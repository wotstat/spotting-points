import time

from .layout_solver import (CALLOUT_GAP, EPSILON, SCREEN_MARGIN,
                            CalloutLayoutSolver, _clamp, _octilinearLeader,
                            rectangleIntersectionArea, _polylinesIntersect,
                            _polylineLength, rectanglePolygonIntersectionArea)


LABEL_GAP = 6.0
LAYOUT_SWITCH_MARGIN = 48.0
ORDER_DEADBAND = 8.0
HYSTERESIS_SECONDS = 0.8
HYSTERESIS_RECHECK_SECONDS = 0.05


class SideLayoutSolver(CalloutLayoutSolver):
    """Place short horizontal leaders first; move only colliding labels."""

    def __init__(self, clock=None):
        super(SideLayoutSolver, self).__init__()
        self._clock = clock or time.clock
        self._holdStarted = None
        self._recheckAt = None
        self._orderHolds = {}
        self._orderDeltas = {}

    def reset(self):
        super(SideLayoutSolver, self).reset()
        self._holdStarted = None
        self._recheckAt = None
        self._orderHolds = {}
        self._orderDeltas = {}

    def solve(self, width, height, hullPoints, turretPoints, items):
        now = self._clock()
        items = sorted(items, key=lambda item: str(item['id']))
        signature = self._inputSignature(
            width, height, hullPoints, turretPoints, items)
        if (signature == self._signature
                and (self._recheckAt is None or now < self._recheckAt)):
            self.lastChanged = False
            return {'revision': self._revision}

        geometry = self._buildGeometry(hullPoints, turretPoints)
        self._prepareOrder(items, now)
        obstacles = (geometry['hull'], geometry['turret'])
        spanCache = {}
        self.candidateCount = 0

        def candidate(item, lane, centerY):
            self.candidateCount += 1
            if lane == 'top':
                return self._verticalCandidate(item, obstacles, float(width), float(height))
            return self._sideCandidate(
                item, lane, (centerY - float(item['y'])) / CALLOUT_GAP,
                0, obstacles, float(width), float(height), spanCache)

        pending = []
        for item in items:
            sides = [candidate(item, lane, float(item['y']))
                     for lane in ('left', 'right')]
            sides = [side for side in sides if side is not None]
            if not sides:
                # Keep a callout even when its anchor is outside the viewport.
                clipped = dict(item)
                halfHeight = float(item['height']) * 0.5
                clipped['y'] = _clamp(float(item['y']),
                                      SCREEN_MARGIN + halfHeight,
                                      max(SCREEN_MARGIN + halfHeight,
                                          height - SCREEN_MARGIN - halfHeight))
                sides = [candidate(clipped, lane, clipped['y'])
                         for lane in ('left', 'right')]
                for side in sides:
                    side['leader'] = _octilinearLeader(
                        (float(item['x']), float(item['y'])),
                        side['leader'][-1])
            baseline = min(sides, key=lambda side: (
                _polylineLength(side['leader']), side['lane']))
            if str(item['id']) == 'top':
                above = candidate(item, 'top', float(item['y']))
                if (above is not None and _polylineLength(above['leader']) + EPSILON
                        < _polylineLength(baseline['leader'])):
                    baseline = above
            pending.append((_polylineLength(baseline['leader']),
                            str(item['id']), item, baseline))

        placed = []
        for unusedLength, pointId, item, baseline in sorted(pending):
            chosen = baseline
            if (self._overlap(baseline, placed) > EPSILON
                    or any(_polylinesIntersect(baseline['leader'], entry['leader'])
                           for entry in placed)):
                halfHeight = float(item['height']) * 0.5
                rows = set((float(item['y']),))
                for existing in placed:
                    rect = existing['rect']
                    rows.add(rect[1] - LABEL_GAP - halfHeight)
                    rows.add(rect[1] + rect[3] + LABEL_GAP + halfHeight)
                options = [baseline]
                for lane in ('left', 'right'):
                    for row in sorted(rows):
                        option = candidate(item, lane, row)
                        if option is not None:
                            options.append(option)
                chosen = min(options, key=lambda option: self._rank(
                    option, item, placed, baseline['lane']))
            chosen['id'] = pointId
            placed.append(chosen)

        # Keep the previous choices in current geometry, not frozen pixels.
        # The six-pixel label gap provides room for small relative movements.
        holding = False
        if self._lastResult is not None:
            previous = self._lastResult['placements']
            freshById = dict((entry['id'], entry) for entry in placed)
            itemById = dict((str(item['id']), item) for item in items)
            if set(itemById) == set(entry['id'] for entry in previous):
                retained = []
                hasHeldChoice = False
                for entry in previous:
                    item = itemById[entry['id']]
                    offset = (entry['rect'][1] + entry['rect'][3] * 0.5
                              - entry['leader'][0][1])
                    choice = candidate(item, entry['lane'], float(item['y']) + offset)
                    if choice is None:
                        break
                    fresh = freshById[entry['id']]
                    # Sub-row motion on the same side is continuous: use the
                    # newly solved position, even while other labels are held.
                    # A full row jump or a side change still needs hysteresis.
                    if (fresh['lane'] == choice['lane']
                            and abs(fresh['rect'][1] - choice['rect'][1])
                            < float(item['height']) * 0.5):
                        choice = fresh
                    else:
                        hasHeldChoice = True
                    choice['id'] = entry['id']
                    retained.append(choice)
                if len(retained) == len(previous):
                    oldScore = self._stabilityScore(retained)
                    newScore = self._stabilityScore(placed)
                    started = now if self._holdStarted is None else self._holdStarted
                    strength = max(0.0, 1.0 - (now - started) / HYSTERESIS_SECONDS)
                    if (strength > 0.0
                            and all(a <= b for a, b in zip(oldScore[:3], newScore[:3]))
                            and oldScore[3] <= newScore[3] + LAYOUT_SWITCH_MARGIN * strength):
                        placed = retained
                        self.stablePlanHits += 1
                        holding = hasHeldChoice
                        if holding:
                            self._holdStarted = started

        # Revisit a pending choice even if the camera input is cached.
        # Continuous motion does not restart this countdown.
        if holding:
            self._recheckAt = min(now + HYSTERESIS_RECHECK_SECONDS,
                                  self._holdStarted + HYSTERESIS_SECONDS)
        else:
            self._holdStarted = None
            self._recheckAt = None
        if self._orderHolds:
            self._recheckAt = now + HYSTERESIS_RECHECK_SECONDS

        self._revision += 1
        self._signature = signature
        self.lastChanged = True
        self.fullSearches += 1
        self._lastResult = self._serializeResult(
            geometry, {'entries': placed, 'score': ()})
        return self._lastResult

    def _prepareOrder(self, items, now):
        # Stabilize the discrete pair order before generating rows. Holding
        # old pixel offsets afterwards can already cause overlaps/crossings.
        self._orderDeltas = {}
        previous = dict((entry['id'], entry) for entry in
                        (self._lastResult['placements'] if self._lastResult else []))
        holds = {}
        for index, item in enumerate(items):
            pointId = str(item['id'])
            for other in items[index + 1:]:
                otherId = str(other['id'])
                a, b = previous.get(pointId), previous.get(otherId)
                if a is None or b is None or a['lane'] != b['lane']:
                    continue
                delta = float(item['y']) - float(other['y'])
                oldDelta = (a['rect'][1] + a['rect'][3] * 0.5
                            - b['rect'][1] - b['rect'][3] * 0.5)
                key = (pointId, otherId)
                if delta * oldDelta <= 0 and abs(oldDelta) > EPSILON:
                    started = self._orderHolds.get(key, now)
                    strength = max(0.0, 1.0 - (now - started) / HYSTERESIS_SECONDS)
                    if strength > 0 and abs(delta) < ORDER_DEADBAND * strength:
                        holds[key] = started
                        self._orderDeltas[key] = oldDelta
        self._orderHolds = holds

    def _orderDelta(self, pointId, otherId, delta):
        if pointId < otherId:
            return self._orderDeltas.get((pointId, otherId), delta)
        return -self._orderDeltas.get((otherId, pointId), -delta)

    def _verticalCandidate(self, item, obstacles, width, height):
        if str(item['id']) != 'top':
            return None
        entry = self._topCandidate(item, 0, 0, obstacles, width, height)
        rect = entry['rect']
        # Reject edge clamping that would bend the vertical line or put the
        # label into the vehicle. Side slots remain available in those cases.
        if (abs(rect[0] + rect[2] * 0.5 - float(item['x'])) > EPSILON
                or rect[1] + rect[3] >= float(item['y'])
                or any(rectanglePolygonIntersectionArea(rect, obstacle['obstacle'])
                       > EPSILON for obstacle in obstacles)):
            return None
        return entry

    def _stabilityScore(self, entries):
        overlap = 0.0
        crossings = 0
        inversions = 0
        cost = 0.0
        for index, entry in enumerate(entries):
            center = entry['rect'][1] + entry['rect'][3] * 0.5
            cost += (_polylineLength(entry['leader'])
                     + abs(center - entry['leader'][0][1]) * 4.0)
            for other in entries[index + 1:]:
                overlap += rectangleIntersectionArea(entry['rect'], other['rect'])
                crossings += int(_polylinesIntersect(entry['leader'], other['leader']))
                delta = entry['leader'][0][1] - other['leader'][0][1]
                delta = self._orderDelta(entry['id'], other['id'], delta)
                otherCenter = other['rect'][1] + other['rect'][3] * 0.5
                if entry['lane'] == other['lane']:
                    inversions += int(delta * (center - otherCenter) < -EPSILON)
        return (0.0 if overlap < EPSILON else overlap, crossings, inversions, cost)

    def _overlap(self, candidate, placed):
        x, y, width, height = candidate['rect']
        padded = (x, y - LABEL_GAP, width, height + LABEL_GAP * 2)
        area = sum(rectangleIntersectionArea(padded, entry['rect'])
                   for entry in placed)
        return 0.0 if area < EPSILON else area

    def _rank(self, candidate, item, placed, preferredLane):
        centerY = candidate['rect'][1] + candidate['rect'][3] * 0.5
        displacement = abs(centerY - float(item['y']))
        crossings = 0
        inversions = 0
        for existing in placed:
            crossings += int(_polylinesIntersect(
                candidate['leader'], existing['leader']))
            if existing['lane'] == candidate['lane']:
                otherCenter = existing['rect'][1] + existing['rect'][3] * 0.5
                pointDelta = float(item['y']) - existing['leader'][0][1]
                pointDelta = self._orderDelta(str(item['id']), existing['id'], pointDelta)
                inversions += int(pointDelta * (centerY - otherCenter)
                                  < -EPSILON)
        rowHeight = float(item['height']) + LABEL_GAP
        length = _polylineLength(candidate['leader'])
        cost = length + displacement * 4.0 + rowHeight * 2.0 * (
            candidate['lane'] != preferredLane)
        return (self._overlap(candidate, placed), inversions, crossings,
                cost, displacement, centerY, candidate['lane'])
