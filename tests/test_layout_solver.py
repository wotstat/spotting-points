import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class LayoutSolverTests(unittest.TestCase):
    def _box(self, left, top, right, bottom):
        return [(left, top), (right, top), (right, bottom), (left, bottom)]

    def _item(self, pointId, x, y, width=64.0, height=24.0,
              part='hull'):
        return {'id': pointId, 'x': x, 'y': y, 'width': width,
                'height': height, 'part': part}

    def test_geometry_and_candidates_are_symmetric(self):
        from wotstat_spotting_points.layout_solver import (
            CalloutLayoutSolver, convexHull,
            rectanglePolygonIntersectionArea)

        square = [(40.0, 40.0), (80.0, 40.0),
                  (80.0, 80.0), (40.0, 80.0)]
        self.assertEqual(convexHull(square + square[:2]), square)
        self.assertAlmostEqual(
            rectanglePolygonIntersectionArea(
                (60.0, 60.0, 30.0, 30.0), square),
            400.0)

        projected = [(130.0, 80.0), (170.0, 80.0),
                     (170.0, 120.0), (130.0, 120.0)]
        solver = CalloutLayoutSolver()
        geometry = solver._buildGeometry(projected, projected)
        candidates = solver._buildCandidates({
            'id': 'front', 'x': 150.0, 'y': 100.0,
            'width': 50.0, 'height': 24.0, 'part': 'hull'
        }, geometry, 400.0, 300.0)

        top = [candidate for candidate in candidates
               if candidate['lane'] == 'top']
        side = [candidate for candidate in candidates
                if candidate['lane'] in ('left', 'right')]
        verticalDirections = set(
            cmp(candidate['leader'][-1][1], 100.0) for candidate in side)
        self.assertEqual(len(top), 5)
        self.assertEqual(verticalDirections, set((-1, 0, 1)))
        for candidate in side:
            leader = candidate['leader']
            self.assertEqual(len(leader), 3)
            self.assertAlmostEqual(abs(leader[1][0] - leader[0][0]),
                                   abs(leader[1][1] - leader[0][1]))
            self.assertAlmostEqual(leader[1][1], leader[2][1])

    def test_solver_can_use_multiple_top_placements(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        class CountingSolver(CalloutLayoutSolver):
            def __init__(self):
                CalloutLayoutSolver.__init__(self)
                self.pairScoreCalls = 0

            def _pairScore(self, first, second):
                self.pairScoreCalls += 1
                return CalloutLayoutSolver._pairScore(self, first, second)

        solver = CountingSolver()
        result = solver.solve(
            640.0, 400.0,
            self._box(80.0, 150.0, 560.0, 300.0),
            self._box(220.0, 110.0, 420.0, 210.0),
            [self._item('left', 180.0, 210.0),
             self._item('top', 320.0, 140.0),
             self._item('right', 460.0, 210.0)])

        lanes = [placement['lane'] for placement in result['placements']]
        self.assertGreaterEqual(lanes.count('top'), 2)
        topRects = [placement['rect'] for placement in result['placements']
                    if placement['lane'] == 'top']
        self.assertEqual(len(topRects), len(set(tuple(rect)
                                                for rect in topRects)))
        self.assertLess(solver.pairScoreCalls, 250)

    def test_top_leaders_are_octilinear_and_enter_bottom_center(self):
        from wotstat_spotting_points.layout_solver import (
            CalloutLayoutSolver, _octilinearLeader)

        routes = (
            ((0.0, 0.0), (0.0, 0.0),
             [(0.0, 0.0), (0.0, 0.0)]),
            ((0.0, 0.0), (0.0, 10.0),
             [(0.0, 0.0), (0.0, 10.0)]),
            ((0.0, 0.0), (10.0, 0.0),
             [(0.0, 0.0), (10.0, 0.0)]),
            ((0.0, 0.0), (10.0, 10.0),
             [(0.0, 0.0), (10.0, 10.0)]),
            ((0.0, 0.0), (10.0, 4.0),
             [(0.0, 0.0), (6.0, 0.0), (10.0, 4.0)]),
            ((0.0, 0.0), (4.0, 10.0),
             [(0.0, 0.0), (4.0, 4.0), (4.0, 10.0)]),
            ((0.0, 0.0), (0.00005, 10.0),
             [(0.0, 0.0), (0.00005, 0.00005),
              (0.00005, 10.0)]))
        for start, target, expected in routes:
            self.assertEqual(_octilinearLeader(start, target), expected)

        projected = self._box(130.0, 80.0, 170.0, 120.0)
        solver = CalloutLayoutSolver()
        geometry = solver._buildGeometry(projected, projected)
        candidates = solver._buildCandidates(
            self._item('top', 150.0, 100.0, 50.0),
            geometry, 500.0, 300.0)

        topCandidates = [candidate for candidate in candidates
                         if candidate['lane'] == 'top']
        self.assertEqual(len(topCandidates), 5)
        for candidate in topCandidates:
            boxX, boxY, boxWidth, boxHeight = candidate['rect']
            self.assertEqual(candidate['leader'][-1],
                             (boxX + boxWidth * 0.5,
                              boxY + boxHeight))
            for point in candidate['leader'][:-1]:
                self.assertNotEqual(point[1], boxY + boxHeight)
            for start, end in zip(candidate['leader'],
                                  candidate['leader'][1:]):
                deltaX = abs(end[0] - start[0])
                deltaY = abs(end[1] - start[1])
                if deltaX > 0.0001 and deltaY > 0.0001:
                    self.assertAlmostEqual(deltaX, deltaY)

    def test_solver_returns_complete_plan_inside_forbidden_zone(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        items = [self._item('front', 145.0, 100.0, 100.0),
                 self._item('rear', 155.0, 120.0, 100.0)]
        result = CalloutLayoutSolver().solve(
            300.0, 220.0, self._box(0.0, 0.0, 300.0, 220.0),
            self._box(60.0, 40.0, 240.0, 180.0), items)

        self.assertEqual(set(item['id'] for item in items),
                         set(placement['id']
                             for placement in result['placements']))
        self.assertGreater(result['score'][7], 0)

    def test_pair_cost_uses_strict_conflict_priority(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        solver = CalloutLayoutSolver()
        crossing = solver._pairScore(
            {'point': (10.0, 10.0), 'rect': (80.0, 80.0, 20.0, 10.0),
             'leader': [(10.0, 10.0), (90.0, 70.0)]},
            {'point': (10.0, 70.0), 'rect': (80.0, 0.0, 20.0, 10.0),
             'leader': [(10.0, 70.0), (90.0, 10.0)]})
        overlapping = solver._pairScore(
            {'point': (10.0, 10.0), 'rect': (80.0, 80.0, 20.0, 10.0),
             'leader': [(10.0, 10.0), (40.0, 40.0)]},
            {'point': (10.0, 70.0), 'rect': (85.0, 84.0, 20.0, 10.0),
             'leader': [(10.0, 70.0), (40.0, 50.0)]})
        throughPoint = solver._pairScore(
            {'point': (10.0, 10.0), 'rect': (80.0, 80.0, 20.0, 10.0),
             'leader': [(10.0, 10.0), (90.0, 10.0)]},
            {'point': (50.0, 10.0), 'rect': (80.0, 40.0, 20.0, 10.0),
             'leader': [(50.0, 10.0), (90.0, 40.0)]})

        self.assertEqual(crossing[4], 1)
        self.assertEqual(overlapping[2], 1)
        self.assertEqual(throughPoint[0], 1)
        self.assertLess(crossing, overlapping)
        self.assertLess(overlapping, throughPoint)

    def test_sub_epsilon_area_noise_is_normalized_out_of_scores(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        solver = CalloutLayoutSolver()
        geometry = {
            'hull': {'bounds': (40.0, 40.0, 60.0, 60.0),
                     'obstacle': self._box(40.0, 40.0, 60.0, 60.0)},
            'turret': {'bounds': (140.0, 140.0, 160.0, 160.0),
                       'obstacle': self._box(140.0, 140.0, 160.0, 160.0)}
        }
        item = self._item('front', 20.0, 20.0, 20.0, 10.0)
        candidate = {
            'lane': 'left',
            'rect': (8.0 - 1.0e-9, 8.0, 20.0, 10.0),
            'leader': [(20.0, 20.0), (8.0, 20.0)]
        }
        localScore = solver._candidateScore(
            item, candidate, geometry, 200.0, 200.0)
        pairScore = solver._pairScore(
            {'point': (0.0, 30.0),
             'rect': (0.0, 0.0, 20.0, 10.0),
             'leader': [(0.0, 30.0), (0.0, 40.0)]},
            {'point': (50.0, 30.0),
             'rect': (20.0 - 1.0e-9, 0.0, 20.0, 10.0),
             'leader': [(50.0, 30.0), (50.0, 40.0)]})

        self.assertEqual(localScore[:2], (0, 0.0))
        self.assertEqual(pairScore[2:4], (0, 0.0))

    def test_cache_lane_hysteresis_and_reset(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        solver = CalloutLayoutSolver()
        hull = self._box(120.0, 90.0, 280.0, 210.0)
        turret = self._box(160.0, 60.0, 240.0, 140.0)
        items = [self._item('front', 200.0, 180.0)]
        first = solver.solve(400.0, 300.0, hull, turret, items)
        cached = solver.solve(400.04, 300.04, hull, turret, items)

        self.assertEqual(first['revision'], 1)
        self.assertEqual(cached, {'revision': 1})
        firstChoice = dict(solver._lastChoiceByPointId)
        shiftedHull = [(point[0] + 0.5, point[1]) for point in hull]
        shiftedTurret = [(point[0] + 0.5, point[1])
                         for point in turret]
        shiftedItems = [dict(items[0], x=items[0]['x'] + 0.5)]
        shifted = solver.solve(
            400.0, 300.0, shiftedHull, shiftedTurret, shiftedItems)
        self.assertEqual(solver.candidateCount, 1)
        self.assertEqual(solver._lastChoiceByPointId, firstChoice)
        self.assertEqual(shifted['revision'], 2)
        selectedLane = first['placements'][0]['lane']
        sameLane = {'lane': selectedLane,
                    'leader': [(0.0, 0.0), (20.0, 0.0)]}
        otherLane = {'lane': ('right' if selectedLane != 'right' else 'left'),
                     'leader': [(0.0, 0.0), (20.0, 0.0)]}
        self.assertGreater(solver._ordinaryCost(items[0], otherLane),
                           solver._ordinaryCost(items[0], sameLane))

        solver.reset()
        afterReset = solver.solve(400.0, 300.0, hull, turret, items)
        self.assertEqual(afterReset['revision'], 1)
        self.assertIn('placements', afterReset)

    def test_ordinary_cost_prefers_straight_responsive_routes(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        solver = CalloutLayoutSolver()
        solver._lastLaneByPointId['front'] = 'left'
        item = self._item('front', 0.0, 0.0)
        straight = {'lane': 'left',
                    'leader': [(0.0, 0.0), (200.0, 0.0)]}
        bent = {'lane': 'left',
                'leader': [(0.0, 0.0), (100.0, 0.0),
                           (100.0, 100.0)]}
        duplicatePoint = {'lane': 'left',
                          'leader': [(0.0, 0.0), (0.0, 0.0),
                                     (200.0, 0.0)]}
        shorterOtherLane = {'lane': 'right',
                            'leader': [(0.0, 0.0), (110.0, 0.0)]}

        self.assertGreater(solver._ordinaryCost(item, bent),
                           solver._ordinaryCost(item, straight))
        self.assertEqual(solver._ordinaryCost(item, duplicatePoint),
                         solver._ordinaryCost(item, straight))
        self.assertLess(solver._ordinaryCost(item, shorterOtherLane),
                        solver._ordinaryCost(item, straight))

    def test_conflict_repair_repolishes_routes_after_labels_move(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        hull = [
            (686.6051635742188, 576.7189331054688),
            (668.887451171875, 505.180419921875),
            (1163.9197998046875, 467.74365234375),
            (1149.2247314453125, 536.6398315429688),
            (659.4413452148438, 730.597412109375),
            (633.9708862304688, 652.5147705078125),
            (1263.89453125, 591.2153930664062),
            (1237.7611083984375, 667.3097534179688)]
        turret = [
            (972.1363525390625, 451.4009704589844),
            (975.1876220703125, 369.88922119140625),
            (1143.564453125, 481.37554931640625),
            (1124.9554443359375, 575.7683715820312),
            (788.280029296875, 498.593017578125),
            (776.64453125, 411.6543884277344),
            (901.2666015625, 554.95263671875),
            (904.1818237304688, 655.107666015625)]
        items = [
            self._item('front', 1198.0015869140625, 559.8545532226562,
                       130.7),
            self._item('gunMoving', 995.3472900390625, 557.4804077148438,
                       183.8, part='turret'),
            self._item('gunStatic', 1027.04345703125, 515.1535034179688,
                       188.45, part='turret'),
            self._item('left', 925.9006958007812, 464.2854919433594,
                       162.45),
            self._item('rear', 664.5592651367188, 608.4660034179688,
                       118.2),
            self._item('right', 965.4091186523438, 596.2081298828125,
                       168.55),
            self._item('top', 930.5712890625, 457.0800476074219,
                       170.65)]
        solver = CalloutLayoutSolver()
        solver._lastLaneByPointId.update({
            'front': 'top', 'gunMoving': 'left', 'gunStatic': 'top',
            'left': 'left', 'rear': 'left', 'right': 'right',
            'top': 'left'})

        result = solver.solve(3257.0, 2055.0, hull, turret, items)

        front = [placement for placement in result['placements']
                 if placement['id'] == 'front'][0]
        nonZeroSegments = [
            (end[0] - start[0], end[1] - start[1])
            for start, end in zip(front['leader'], front['leader'][1:])
            if (abs(end[0] - start[0]) > 0.0001
                or abs(end[1] - start[1]) > 0.0001)]
        self.assertEqual(len(nonZeroSegments), 1)

    def test_stable_conflict_repairs_only_participating_labels(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        solver = CalloutLayoutSolver()
        hull = self._box(120.0, 90.0, 280.0, 210.0)
        turret = self._box(160.0, 60.0, 240.0, 140.0)
        solver.solve(
            400.0, 300.0, hull, turret,
            [self._item('a', 150.0, 80.0, 100.0),
             self._item('b', 250.0, 200.0, 100.0)])

        result = solver.solve(
            400.0, 300.0, hull, turret,
            [self._item('a', 150.5, 80.0, 100.0),
             self._item('b', 250.0, 80.5, 100.0)])

        self.assertEqual(result['score'][2:7], [0, 0.0, 0, 0.0, 0])
        self.assertEqual(solver.fullSearches, 1)
        self.assertEqual(solver.stablePlanHits, 1)
        self.assertLessEqual(solver.candidateCount, 32)

    def test_stable_plan_repairs_a_persistent_conflict(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        solver = CalloutLayoutSolver()
        solver._signature = ('previous-frame',)
        solver._lastResult = {
            'score': [0, 0.0, 0, 0.0, 0, 0.0, 1, 0, 0.0, 0.0]
        }
        solver._lastLaneByPointId.update({'a': 'right', 'b': 'left'})
        solver._lastChoiceByPointId.update({
            'a': ('right', 1),
            'b': ('left', 1)
        })

        result = solver.solve(
            400.0, 300.0,
            self._box(120.0, 90.0, 280.0, 210.0),
            self._box(160.0, 60.0, 240.0, 140.0),
            [self._item('a', 150.0, 80.0, 100.0),
             self._item('b', 250.0, 80.5, 100.0)])

        self.assertEqual(result['score'][2:7], [0, 0.0, 0, 0.0, 0])
        self.assertEqual(solver.stablePlanHits, 1)
        self.assertEqual(solver.fullSearches, 0)

    def test_lane_switch_does_not_raise_reconsideration_baseline(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        class SwitchingSolver(CalloutLayoutSolver):
            def _search(self, items, geometry, width, height):
                item = items[0]
                entry = {
                    'id': str(item['id']),
                    'lane': 'right',
                    'offsetIndex': 0,
                    'rect': (8.0, 8.0, 64.0, 24.0),
                    'leader': [(0.0, 0.0), (20.0, 0.0)],
                    'point': (float(item['x']), float(item['y']))
                }
                entry['_localScore'] = self._candidateScore(
                    item, entry, geometry, width, height)
                entry['_signature'] = self._candidateSignature(entry)
                return {'score': entry['_localScore'],
                        'signature': entry['_signature'],
                        'entries': [entry]}

        solver = SwitchingSolver()
        solver._lastLaneByPointId['front'] = 'left'
        hull = self._box(120.0, 90.0, 280.0, 210.0)
        turret = self._box(160.0, 60.0, 240.0, 140.0)
        solver.solve(
            400.0, 300.0, hull, turret,
            [self._item('front', 200.0, 180.0)])

        baseline = solver._lastEvaluatedCostByPointId['front']
        grown = {'lane': 'right',
                 'leader': [(0.0, 0.0), (85.0, 0.0)]}
        self.assertEqual(baseline, 20.0)
        self.assertGreater(solver._leaderCost(grown), baseline + 64.0)


if __name__ == '__main__':
    unittest.main()
