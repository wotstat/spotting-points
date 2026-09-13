# -*- coding: utf-8 -*-
import importlib
import math
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
        self.yaw = getattr(source, 'yaw', 0.0)
        self.translation = getattr(source, 'translation', (0.0, 0.0, 0.0))
        self._inverted = False

    def setTranslate(self, point):
        self.translation = point

    def invert(self):
        self._inverted = not self._inverted

    def applyPoint(self, point):
        cosine = math.cos(self.yaw)
        sine = math.sin(self.yaw)
        tx, ty, tz = self.translation
        x, y, z = point
        if self._inverted:
            x -= tx
            y -= ty
            z -= tz
            return (cosine * x - sine * z, y,
                    sine * x + cosine * z)
        return (tx + cosine * x + sine * z, ty + y,
                tz - sine * x + cosine * z)


class FakeMatrixProduct(object):
    def __init__(self):
        self.a = None
        self.b = None

    def applyToOrigin(self):
        return self.b.applyPoint(self.a.applyPoint((0.0, 0.0, 0.0)))


class FakeNativeMarker(object):
    def __init__(self):
        self.marker = None
        self.provider = None
        self.active = []

    def setMarker(self, marker, provider):
        self.marker = marker
        self.provider = provider

    def markerSetActive(self, value):
        self.active.append(value)


class FakeFlash(object):
    def __init__(self):
        self.created = []
        self.layoutCreated = []
        self.updated = []
        self.removed = []

    def as_createMarker(self, pointId, label):
        marker = object()
        self.created.append((pointId, label, marker))
        return marker

    def as_updateMarkers(self, data, hoveredPointId):
        self.updated.append((data, hoveredPointId))

    def as_createLayoutAnchor(self, anchorId):
        marker = object()
        self.layoutCreated.append((anchorId, marker))
        return marker

    def as_removeMarker(self, pointId):
        self.removed.append(pointId)


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _loadMarkerViewModule(currentRealm='RU'):
    nativeMarkers = []

    def createNativeMarker():
        marker = FakeNativeMarker()
        nativeMarkers.append(marker)
        return marker

    _module('GUI', HangarVehicleMarker=createNativeMarker)
    _module('Math', Matrix=FakeMatrix, MatrixProduct=FakeMatrixProduct)
    _module('realm', CURRENT_REALM=currentRealm)
    _module('frameworks')
    _module('frameworks.wulf', WindowLayer=Bag(
        FULLSCREEN_WINDOW=1, OVERLAY=2, SUB_VIEW=3,
        TOP_SUB_VIEW=4, MARKER=5))
    _module('gui')
    _module('gui.Scaleform')
    _module('gui.Scaleform.daapi')
    _module('gui.Scaleform.daapi.settings')
    _module('gui.Scaleform.daapi.settings.views', VIEW_ALIAS=Bag(
        LOBBY_HANGAR='hangar'))
    _module('gui.Scaleform.framework', ScopeTemplates=Bag(DEFAULT_SCOPE=None),
            ViewSettings=object, g_entitiesFactories=object())
    _module('gui.Scaleform.framework.entities')
    _module('gui.Scaleform.framework.entities.View', View=object,
            ViewKey=object)
    _module('gui.Scaleform.framework.managers')
    _module('gui.Scaleform.framework.managers.loaders', SFViewLoadParams=object)
    _module('helpers', dependency=Bag(instance=lambda cls: None))
    _module('skeletons')
    _module('skeletons.gui')
    _module('skeletons.gui.app_loader', IAppLoader=object)
    _module('skeletons.gui.impl', IGuiLoader=object)
    _module('vehicle_systems')
    _module('vehicle_systems.tankStructure',
            TankNodeNames=Bag(GUN_JOINT='gunJoint'),
            TankPartNames=Bag(HULL='hull', TURRET='turret'))
    sys.modules.pop('wotstat_spotting_points.marker_view', None)
    module = importlib.import_module('wotstat_spotting_points.marker_view')
    return module, nativeMarkers


class MarkerViewTests(unittest.TestCase):
    def test_layout_bounds_use_live_hull_and_turret_providers(self):
        markerView, nativeMarkers = _loadMarkerViewModule()
        from wotstat_spotting_points.geometry import LayoutBounds
        flash = FakeFlash()
        hullProvider = FakeMatrix()
        hullProvider.translation = (10.0, 1.0, 20.0)
        turretProvider = FakeMatrix()
        turretProvider.yaw = math.pi / 2.0
        turretProvider.translation = (10.0, 4.0, 20.0)
        partProviders = {'hull': hullProvider, 'turret': turretProvider}
        vehicle = Bag(model=Bag(node=lambda name: partProviders[name]))
        view = object.__new__(markerView.MarkerOverlayView)
        view._ready = True
        view._sceneActive = True
        view._nativeMarkers = {}
        view._layoutMarkers = {}
        view.flashObject = flash
        layoutBounds = LayoutBounds(
            [(-2, 0, -3), (-2, 2, -3), (-2, 2, 3), (-2, 0, 3),
             (2, 0, -3), (2, 2, -3), (2, 2, 3), (2, 0, 3)],
            [(-1, 0, -1), (-1, 1, -1), (-1, 1, 1), (-1, 0, 1),
             (1, 0, -1), (1, 1, -1), (1, 1, 1), (1, 0, 1)])

        view.updateMarkers([], vehicle, None, layoutBounds)

        self.assertEqual(len(nativeMarkers), 16)
        self.assertEqual([item[0] for item in flash.layoutCreated],
                         ['hull%d' % index for index in range(8)] +
                         ['turret%d' % index for index in range(8)])
        self.assertIs(view._layoutMarkers['hull0'].provider.b,
                      hullProvider)
        self.assertIs(view._layoutMarkers['turret0'].provider.b,
                      turretProvider)
        translated = view._layoutMarkers['turret6'].provider.applyToOrigin()
        expected = turretProvider.applyPoint(layoutBounds.turret[6])
        for actual, wanted in zip(translated, expected):
            self.assertAlmostEqual(actual, wanted)
        self.assertTrue(all(marker.active == [True]
                            for marker in nativeMarkers))

    def test_native_markers_follow_vehicle_and_gun_matrix_providers(self):
        markerView, nativeMarkers = _loadMarkerViewModule()
        from wotstat_spotting_points.marker_logic import MarkerData
        flash = FakeFlash()
        gunProvider = object()
        vehicleMatrix = FakeMatrix()
        vehicleMatrix.yaw = math.pi / 2.0
        vehicleMatrix.translation = (10.0, 0.0, 20.0)
        vehicle = Bag(matrix=vehicleMatrix, model=Bag(
            node=lambda name: gunProvider))
        view = object.__new__(markerView.MarkerOverlayView)
        view._ready = True
        view._sceneActive = True
        view._nativeMarkers = {}
        view._layoutMarkers = {}
        view.flashObject = flash
        markers = [
            MarkerData('front', (15.0, 0.0, 20.0), u'Передняя'),
            MarkerData('gunMoving', (4, 5, 6), u'Орудийная'),
        ]

        view.updateMarkers(markers, vehicle, 'front')

        self.assertEqual(len(nativeMarkers), 2)
        frontProvider = nativeMarkers[0].provider
        self.assertIsInstance(frontProvider, FakeMatrixProduct)
        for actual, expected in zip(frontProvider.a.translation,
                                    (0.0, 0.0, 5.0)):
            self.assertAlmostEqual(actual, expected)
        self.assertIs(frontProvider.b, vehicleMatrix)
        for actual, expected in zip(frontProvider.applyToOrigin(),
                                    markers[0].point):
            self.assertAlmostEqual(actual, expected)
        self.assertIs(nativeMarkers[1].provider, gunProvider)
        self.assertEqual(nativeMarkers[0].active, [True])
        self.assertTrue(all(item['showLabel']
                            for item in flash.updated[-1][0]))

        view.updateMarkers(markers[1:], vehicle, None)

        self.assertEqual(nativeMarkers[0].active[-1], False)
        self.assertEqual(flash.removed, ['front'])

    def test_popover_blocks_overlay_only_in_wot_eu(self):
        popover = type('PopOverWindow', (object,), {})()

        markerView, _ = _loadMarkerViewModule('RU')
        self.assertTrue(markerView._isBaseHangarWindow(popover))

        markerView, _ = _loadMarkerViewModule('EU')
        self.assertFalse(markerView._isBaseHangarWindow(popover))


if __name__ == '__main__':
    unittest.main()
