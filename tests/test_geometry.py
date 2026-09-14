import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class GeometryTests(unittest.TestCase):
    def test_layout_bounds_ignore_radius_and_keep_corners_part_local(self):
        from wotstat_spotting_points.geometry import buildLayoutBounds
        bounds = buildLayoutBounds(((-2, 1, -3), (2, 4, 3), 5.0),
                                   ((-1, 0, -1), (1, 2, 1), 2.5))

        self.assertEqual(bounds.hull[0], (-2, 1, -3))
        self.assertEqual(bounds.hull[6], (2, 4, 3))
        self.assertEqual(bounds.turret[0], (-1, 0, -1))
        self.assertEqual(bounds.turret[6], (1, 2, 1))

    def test_select_geometry_keeps_visual_groups_independent(self):
        from wotstat_spotting_points.geometry import selectGeometry
        mask = [(0, 0, 0), (1, 0, 0)]
        spots = [(1, 0, 0), (2, 0, 0)]
        lines = ['guide']

        self.assertEqual(selectGeometry(mask, spots, lines,
                                        False, False, False),
                         ([], [], []))
        self.assertEqual(selectGeometry(mask, spots, lines,
                                        True, False, False),
                         (mask, [], []))
        self.assertEqual(selectGeometry(mask, spots, lines,
                                        False, True, False),
                         ([], spots, []))
        self.assertEqual(selectGeometry(mask, spots, lines,
                                        False, False, True),
                         ([], [], lines))

    def test_select_geometry_draws_shared_point_once_as_observation(self):
        from wotstat_spotting_points.geometry import selectGeometry
        mask = [(0, 0, 0), (1, 0, 0)]
        spots = [(1, 0, 0), (2, 0, 0)]

        selectedMask, selectedSpots, _ = selectGeometry(
            mask, spots, [], True, True, False)

        self.assertEqual(selectedMask, [(0, 0, 0)])
        self.assertEqual(selectedSpots, spots)

    def test_dynamic_gun_point_is_added_after_static_mount(self):
        from wotstat_spotting_points.geometry import addMovingGunPoint
        staticMask = ['rear', 'front', 'left', 'right', 'static-gun', 'top']

        mask, spots = addMovingGunPoint(
            staticMask, ['top'], 'moving-gun')

        self.assertEqual(mask, ['rear', 'front', 'left', 'right',
                                'static-gun', 'top', 'moving-gun'])
        self.assertEqual(spots, ['top', 'moving-gun'])
        self.assertEqual(staticMask[4], 'static-gun')

    def test_turret_arc_connects_mount_points_at_constant_radius(self):
        from wotstat_spotting_points.geometry import buildTurretArc

        points = buildTurretArc((1, 2, 3), (1, 3, 5), (3, 3, 3))

        self.assertEqual(points[0], (1, 3, 5))
        self.assertEqual(points[-1], (3, 3, 3))
        self.assertGreater(len(points), 2)
        for point in points:
            radiusSquared = ((point[0] - 1) ** 2
                             + (point[2] - 3) ** 2)
            self.assertAlmostEqual(radiusSquared, 4.0, places=6)
            self.assertAlmostEqual(point[1], 3.0, places=6)

    def test_asymmetric_hull_and_component_offsets(self):
        from wotstat_spotting_points.geometry import buildGeometry
        points, lines = buildGeometry(((-2, 0, -4), (2, 2, 6)),
                                     ((-1, 0, -1), (1, 1, 2)),
                                     (0, 1, 0), (0, 2, 1), (0, 0.5, 0.8))
        self.assertEqual(points[:4], [(0, 2, -4), (0, 2, 6),
                                     (-2, 3.5, 1), (2, 3.5, 1)])
        self.assertEqual(points[4], (0, 3.5, 1.8))
        self.assertEqual(points[5], (0, 4, 0))
        self.assertTrue(any(points[2] in line.points for line in lines))

    def test_bbox_and_alignment_match_reference(self):
        from wotstat_spotting_points.geometry import buildGeometry
        _, lines = buildGeometry(((-2, 0, -4), (2, 2, 6)),
                                 ((-1, 0, -1), (1, 1, 2)),
                                 (0, 1, 0), (0, 2, 1), (0, 0.5, 0.8))
        self.assertEqual(len(lines), 13)
        self.assertEqual([line.color for line in lines], [0xffffff] * 5 + [0x959595] * 8)
        self.assertEqual([line.backColor for line in lines], [None] * 8 + [0x646464] + [None] * 4)
        self.assertEqual(lines[0].points,
                         [(-2, 4, 6), (2, 4, 6), (2, 4, -4), (-2, 4, -4), (-2, 4, 6)])
        # All 12 hull edges, with no mid-height rectangle from the old renderer.
        edges = set(frozenset((a, b)) for line in lines[1:5]
                    for a, b in zip(line.points, line.points[1:]))
        corners = [(x, y, z) for x in (-2, 2) for y in (1, 3) for z in (-4, 6)]
        expectedEdges = set(frozenset((a, b)) for a in corners for b in corners
                            if sum(a[i] != b[i] for i in range(3)) == 1)
        self.assertEqual(edges, expectedEdges)
        self.assertEqual(lines[5].points, [(-2, 1, -4), (-2, 3, 6), (2, 1, 6), (2, 3, -4), (-2, 1, -4)])
        self.assertEqual(lines[6].points, [(2, 1, -4), (-2, 3, -4), (-2, 1, 6), (2, 3, 6), (2, 1, -4)])
        self.assertEqual(lines[7].points, [(-2, 2, 1), (-2, 3.5, 1), (-2, 3.5, 1.8)])
        self.assertEqual(lines[8].points, [(-2, 3.5, 1.8), (2, 3.5, 1.8)])
        self.assertEqual(lines[9].points, [(2, 3.5, 1.8), (2, 3.5, 1), (2, 2, 1)])
        self.assertEqual(lines[10].points, [(0, 4, 1), (0, 4, 0), (0, 0, 0)])
        self.assertEqual(lines[11].points, [(-2, 4, 6), (2, 4, -4)])
        self.assertEqual(lines[12].points, [(-2, 4, -4), (2, 4, 6)])

    def test_tall_hull_sets_top_above_short_turret(self):
        from wotstat_spotting_points.geometry import buildGeometry
        points, _ = buildGeometry(((-1, 0, -1), (1, 5, 1)),
                                  ((-1, 0, -1), (1, 1, 1)),
                                  (0, 0.5, 0), (0, 1, 0), (0, 0, 0))
        self.assertEqual(points[5], (0, 5.5, 0))

    def test_highlight_groups_only_include_semantic_guides(self):
        from wotstat_spotting_points.geometry import (
            buildGeometry, buildHighlightGroups)
        _, lines = buildGeometry(((-2, 0, -4), (2, 2, 6)),
                                 ((-1, 0, -1), (1, 1, 2)),
                                 (0, 1, 0), (0, 2, 1), (0, 0.5, 0.8))

        groups = buildHighlightGroups(lines)

        self.assertEqual(len(groups['front']), 3)
        self.assertEqual(groups['front'][0].points,
                         [(-2, 1, 6), (-2, 3, 6),
                          (2, 3, 6), (2, 1, 6), (-2, 1, 6)])
        self.assertEqual(groups['front'][1].points,
                         [(-2, 3, 6), (2, 1, 6)])
        self.assertEqual(groups['front'][2].points,
                         [(-2, 1, 6), (2, 3, 6)])
        self.assertEqual(len(groups['rear']), 3)
        self.assertEqual(len(groups['left']), 3)
        self.assertEqual(groups['left'][1:], lines[7:9])
        self.assertEqual(len(groups['right']), 3)
        self.assertEqual(groups['right'][1:], lines[8:10])
        self.assertEqual(groups['top'], [lines[0]])
        self.assertEqual(groups['gunStatic'], [lines[8]])

    def test_moving_gun_highlight_includes_dynamic_arc(self):
        from wotstat_spotting_points.geometry import (
            buildGeometry, buildHighlightGroups, LineGeometry)
        _, lines = buildGeometry(((-2, 0, -4), (2, 2, 6)),
                                 ((-1, 0, -1), (1, 1, 2)),
                                 (0, 1, 0), (0, 2, 1), (0, 0.5, 0.8))
        arc = LineGeometry([(0, 3.5, 1.8), (1, 3.5, 1.0)],
                           0x959595, 0x646464)

        groups = buildHighlightGroups(lines + [arc])

        self.assertEqual(groups['gunMoving'], [lines[8], arc])


if __name__ == '__main__':
    unittest.main()
