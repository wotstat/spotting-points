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

    def test_stable_plan_reconsiders_a_stale_route_after_anchor_motion(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        hull = [
            (1099.2952880859375, 579.021240234375),
            (1104.17333984375, 510.7127990722656),
            (897.3971557617188, 654.2291259765625),
            (899.0973510742188, 771.4622192382812),
            (946.9279174804688, 557.9979248046875),
            (947.3572387695312, 495.447509765625),
            (659.1932983398438, 604.8953247070312),
            (670.9761962890625, 706.3532104492188)]
        turret = [
            (1075.98876953125, 533.0747680664062),
            (1081.1541748046875, 447.5212097167969),
            (982.5321655273438, 486.0709533691406),
            (980.1080322265625, 600.630615234375),
            (906.3839111328125, 514.0140380859375),
            (905.6148681640625, 436.8222351074219),
            (763.6038208007812, 466.53741455078125),
            (770.3551635742188, 566.6168823242188)]
        items = [
            self._item('front', 771.8685913085938, 683.1273193359375,
                       130.7),
            self._item('gunMoving', 892.2551879882812, 540.2261352539062,
                       183.8, part='turret'),
            self._item('left', 1033.168212890625, 535.3704223632812,
                       162.45),
            self._item('rear', 1020.7282104492188, 535.8056030273438,
                       118.2),
            self._item('right', 840.9553833007812, 512.9290771484375,
                       168.55),
            self._item('top', 936.3602905273438, 456.0960388183594,
                       170.65)]
        solver = CalloutLayoutSolver()
        solver._signature = ('previous-frame',)
        solver._lastResult = {
            'score': [0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0,
                      955.165601086635]
        }
        solver._lastLaneByPointId.update({
            'front': 'left', 'gunMoving': 'left', 'left': 'right',
            'rear': 'left', 'right': 'left', 'top': 'left'})
        solver._lastChoiceByPointId.update({
            'front': ('left', 0), 'gunMoving': ('left', 0),
            'left': ('right', 0), 'rear': ('left', 3),
            'right': ('left', 0), 'top': ('left', 3)})
        solver._lastEvaluatedCostByPointId.update({
            'front': 140.08587305438323,
            'gunMoving': 166.02436914103487,
            'left': 110.06711404287853,
            'rear': 319.9948877478823,
            'right': 113.75653180774952,
            'top': 79.19595949289332})
        solver._lastEvaluatedPointByPointId = dict(
            (item['id'], (item['x'], item['y'])) for item in items)
        solver._lastEvaluatedPointByPointId['rear'] = (
            items[3]['x'] - 17.0, items[3]['y'])

        result = solver.solve(1920.0, 1080.0, hull, turret, items)

        rear = [placement for placement in result['placements']
                if placement['id'] == 'rear'][0]
        leaderLength = sum(
            ((end[0] - start[0]) ** 2.0
             + (end[1] - start[1]) ** 2.0) ** 0.5
            for start, end in zip(rear['leader'], rear['leader'][1:]))
        self.assertEqual(result['score'][2:7], [0, 0.0, 0, 0.0, 0])
        self.assertEqual(rear['lane'], 'top')
        self.assertLess(leaderLength, 200.0)
        self.assertEqual(solver.fullSearches, 0)

    def test_slot_change_reconsiders_other_labels_before_publishing(self):
        from wotstat_spotting_points.layout_solver import CalloutLayoutSolver

        hull = [
            (878.1111450195312, 601.9274291992188),
            (877.7515869140625, 538.4913940429688),
            (1230.305908203125, 546.0003662109375),
            (1227.076904296875, 646.2731323242188),
            (734.651123046875, 613.67041015625),
            (733.0990600585938, 540.4739990234375),
            (1073.1737060546875, 551.5048217773438),
            (1071.225830078125, 678.5564575195312)]
        turret = [
            (931.8077392578125, 542.4950561523438),
            (931.8176879882812, 467.797119140625),
            (1103.4609375, 452.5777893066406),
            (1101.72705078125, 546.8560791015625),
            (781.6676635742188, 545.364990234375),
            (780.2667236328125, 457.78863525390625),
            (942.22119140625, 435.8610534667969),
            (942.0779418945312, 551.6251220703125)]
        items = [
            self._item('front', 1159.734619140625, 604.8057861328125,
                       130.7),
            self._item('gunMoving', 996.0455322265625, 518.2733764648438,
                       183.8, part='turret'),
            self._item('left', 1014.1589965820312, 519.4000854492188,
                       162.45),
            self._item('rear', 811.0770263671875, 573.5194702148438,
                       118.2),
            self._item('right', 856.6420288085938, 518.1460571289062,
                       168.55),
            self._item('top', 935.2748413085938, 455.34600830078125,
                       170.65)]
        choices = {
            'front': ('right', 1), 'gunMoving': ('right', 2),
            'left': ('right', 0), 'rear': ('left', 0),
            'right': ('right', 1), 'top': ('right', 3)}
        solver = CalloutLayoutSolver()
        solver._signature = ('previous-frame',)
        solver._lastResult = {
            'score': [0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0.0]
        }
        solver._lastChoiceByPointId.update(choices)
        solver._lastLaneByPointId.update(
            (pointId, choice[0]) for pointId, choice in choices.items())
        solver._lastEvaluatedCostByPointId.update(
            (item['id'], 1000.0) for item in items)
        solver._lastEvaluatedPointByPointId.update(
            (item['id'], (item['x'], item['y'])) for item in items)
        solver._lastEvaluatedPointByPointId['front'] = (
            items[0]['x'] - 17.0, items[0]['y'])

        result = solver.solve(1862.0, 1175.0, hull, turret, items)

        right = [placement for placement in result['placements']
                 if placement['id'] == 'right'][0]
        leaderLength = sum(
            ((end[0] - start[0]) ** 2.0
             + (end[1] - start[1]) ** 2.0) ** 0.5
            for start, end in zip(right['leader'], right['leader'][1:]))
        self.assertEqual(result['score'][2:7], [0, 0.0, 0, 0.0, 0])
        self.assertIn(right['lane'], ('left', 'top'))
        self.assertLess(leaderLength, 200.0)

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
