from .layout_solver import (CALLOUT_GAP, EPSILON, SCREEN_MARGIN,
                            CalloutLayoutSolver, _clamp, _octilinearLeader,
                            _polylineLength)


LABEL_GAP = 6.0


class SideLayoutSolver(CalloutLayoutSolver):
    """Pack screen-ordered rows around the shortest leader on each side."""

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
        for lane in ('left', 'right'):
            ordered = sorted((entry for entry in pending if entry[3]['lane'] == lane),
                             key=lambda entry: (float(entry[2]['y']), entry[1]))
            if not ordered:
                continue
            pivot = min(xrange(len(ordered)),
                        key=lambda index: (ordered[index][0], ordered[index][1]))
            anchor = ordered[pivot][3]
            anchor['id'] = ordered[pivot][1]
            placed.append(anchor)
            # Reserve rows outwards from the shortest horizontal leader.
            # An insertion in a crowded group pushes its neighbours as well,
            # so a label cannot jump across another point's screen order.
            for indices, direction in ((xrange(pivot - 1, -1, -1), -1),
                                       (xrange(pivot + 1, len(ordered)), 1)):
                neighbour = anchor
                for index in indices:
                    unusedLength, pointId, item, baseline = ordered[index]
                    halfHeight = float(item['height']) * 0.5
                    rect = neighbour['rect']
                    if direction < 0:
                        row = min(float(item['y']), rect[1] - LABEL_GAP - halfHeight)
                    else:
                        row = max(float(item['y']),
                                  rect[1] + rect[3] + LABEL_GAP + halfHeight)
                    baselineY = baseline['rect'][1] + halfHeight
                    chosen = baseline if abs(row - baselineY) < EPSILON else (
                        candidate(item, lane, row) or baseline)
                    chosen['id'] = pointId
                    placed.append(chosen)
                    neighbour = chosen

        self._revision += 1
        self._signature = signature
        self.lastChanged = True
        self.fullSearches += 1
        self._lastResult = self._serializeResult(
            geometry, {'entries': placed, 'score': ()})
        return self._lastResult
