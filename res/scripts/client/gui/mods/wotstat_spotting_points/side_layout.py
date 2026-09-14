from .layout_solver import (CALLOUT_GAP, EPSILON, SCREEN_MARGIN,
                            CalloutLayoutSolver, _clamp, _octilinearLeader,
                            rectangleIntersectionArea, _polylinesIntersect,
                            _polylineLength)


LABEL_GAP = 6.0


class SideLayoutSolver(CalloutLayoutSolver):
    """Place short horizontal leaders first; move only colliding labels."""

    def solve(self, width, height, hullPoints, turretPoints, items):
        items = sorted(items, key=lambda item: str(item['id']))
        signature = self._inputSignature(
            width, height, hullPoints, turretPoints, items)
        if signature == self._signature:
            self.lastChanged = False
            return {'revision': self._revision}

        geometry = self._buildGeometry(hullPoints, turretPoints)
        obstacles = (geometry['hull'], geometry['turret'])
        spanCache = {}
        self.candidateCount = 0

        def candidate(item, lane, centerY):
            self.candidateCount += 1
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

        self._revision += 1
        self._signature = signature
        self.lastChanged = True
        self.fullSearches += 1
        self._lastResult = self._serializeResult(
            geometry, {'entries': placed, 'score': ()})
        return self._lastResult

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
                inversions += int(pointDelta * (centerY - otherCenter)
                                  < -EPSILON)
        rowHeight = float(item['height']) + LABEL_GAP
        length = _polylineLength(candidate['leader'])
        cost = length + displacement * 4.0 + rowHeight * 2.0 * (
            candidate['lane'] != preferredLane)
        return (self._overlap(candidate, placed), inversions, crossings,
                cost, displacement, centerY, candidate['lane'])
