TRANSITION_SECONDS = 0.25


def _offsetY(entry):
    return entry['rect'][1] - entry['leader'][0][1]


def _relative(entry):
    x, y = entry['leader'][0]
    return ([entry['rect'][0] - x, entry['rect'][1] - y],
            [[point[0] - x, point[1] - y] for point in entry['leader']])


class CalloutTransitions(object):
    """Interpolate display geometry without feeding it back to the solver."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._targets = {}
        self._animations = {}
        self._layout = None
        self._revision = 0

    def apply(self, result, now):
        changed = 'placements' in result
        if changed:
            self._layout = result
            incoming = set(entry['id'] for entry in result['placements'])
            for pointId in list(self._targets):
                if pointId not in incoming:
                    del self._targets[pointId]
                    self._animations.pop(pointId, None)
            for target in result['placements']:
                pointId = target['id']
                previous = self._targets.get(pointId)
                if previous is not None and (
                        previous['lane'] != target['lane']
                        or abs(_offsetY(previous) - _offsetY(target))
                        >= target['rect'][3] * 0.5):
                    visible = self._render(pointId, now)
                    self._animations[pointId] = (now, _relative(visible))
                self._targets[pointId] = target

        if not changed and not self._animations:
            return {'revision': self._revision}
        self._revision += 1
        displayed = dict(self._layout)
        displayed['revision'] = self._revision
        displayed['placements'] = [self._render(entry['id'], now)
                                   for entry in self._layout['placements']]
        return displayed

    def _render(self, pointId, now):
        target = self._targets[pointId]
        animation = self._animations.get(pointId)
        if animation is None:
            return target
        started, (startBox, startLeader) = animation
        progress = max(0.0, (now - started) / TRANSITION_SECONDS)
        if progress >= 1.0:
            del self._animations[pointId]
            return target
        progress = 1.0 - (1.0 - progress) ** 3
        endBox, endLeader = _relative(target)
        anchor = target['leader'][0]

        def interpolate(start, end):
            return [anchor[axis] + start[axis]
                    + (end[axis] - start[axis]) * progress for axis in (0, 1)]

        displayed = dict(target)
        displayed['rect'] = interpolate(startBox, endBox) + target['rect'][2:]
        displayed['leader'] = [list(anchor)]
        for index in xrange(1, max(len(startLeader), len(endLeader))):
            displayed['leader'].append(interpolate(
                startLeader[min(index, len(startLeader) - 1)],
                endLeader[min(index, len(endLeader) - 1)]))
        return displayed
