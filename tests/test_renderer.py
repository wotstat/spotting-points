import importlib
import os
import sys
import types
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class Bag(object):
    def __init__(self, **attributes):
        self.__dict__.update(attributes)


class FakeMatrix(object):
    def __init__(self, source=None):
        pass

    def applyPoint(self, point):
        return tuple(point)

    def invert(self):
        pass


class FakeLine(object):
    def colour(self, value):
        pass

    def zTest(self, value):
        pass

    def zWrite(self, value):
        pass

    def points(self, value):
        DRAWN_LINES.append(list(value))


class FakeSphere(FakeLine):
    def position(self, value):
        pass

    def radius(self, value):
        pass


class FakeDrawer(object):
    def line(self):
        return FakeLine()

    def sphere(self):
        return FakeSphere()


DRAWN_LINES = []


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _loadRendererModule():
    _module('DebugDrawer', DebugDrawer=FakeDrawer)
    _module('Math', Matrix=FakeMatrix, Vector3=lambda value: tuple(value))
    _module('realm', CURRENT_REALM='RU')
    _module('vehicle_systems')
    _module('vehicle_systems.tankStructure',
            TankPartIndexes=Bag(HULL=0, TURRET=1),
            TankNodeNames=Bag(GUN_JOINT='gunJoint'))
    sys.modules.pop('wotstat_spotting_points.renderer', None)
    return importlib.import_module('wotstat_spotting_points.renderer')


class RendererTests(unittest.TestCase):
    def setUp(self):
        del DRAWN_LINES[:]

    def test_world_geometry_carries_ui_highlights_without_3d_hover_lines(self):
        renderer = _loadRendererModule()
        bounds = {
            0: ((-2, 0, -4), (2, 2, 6)),
            1: ((-1, 0, -1), (1, 1, 2)),
        }
        collisions = Bag(getBoundingBox=lambda part: bounds[part])
        descriptor = Bag(
            chassis=Bag(hullPosition=(0, 1, 0)),
            hull=Bag(turretPositions=[(0, 2, 1)]),
            turret=Bag(gunPosition=(0, 0.5, 0.8)))
        gunJoint = Bag(position=(1, 3.5, 1.0))
        vehicle = Bag(
            appearance=Bag(collisions=collisions),
            typeDescriptor=descriptor,
            matrix=FakeMatrix(),
            model=Bag(node=lambda name: gunJoint))

        try:
            geometry = renderer.getWorldGeometry(vehicle, True, True)
        except TypeError as error:
            self.fail('gun-circle generation cannot be selected: %s' % error)

        self.assertEqual(len(geometry), 4)
        maskPoints, spotPoints, lines, highlights = geometry
        self.assertEqual(len(lines), 14)
        self.assertEqual(highlights['top'].bright[0].points[-1], (0, 0, 0))
        self.assertLessEqual(
            len(highlights['gunMoving'].faded[0].points), 37)
        self.assertGreater(len(highlights['gunMoving'].bright[0].points), 2)
        withoutCircle = renderer.getWorldGeometry(vehicle, True, False)
        self.assertEqual(withoutCircle[3]['gunMoving'].faded, [])

        renderer.drawGeometry(geometry, False, False, False, 'front')

        self.assertEqual(DRAWN_LINES, [])


if __name__ == '__main__':
    unittest.main()
