# -*- coding: utf-8 -*-
import importlib
import logging
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


class ProxyList(object):
    def __init__(self, values):
        self._values = values

    def __len__(self):
        return len(self._values)

    def __getitem__(self, index):
        return self._values[index]


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
        self.cleared = 0

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

    def as_clearMarkers(self):
        self.cleared += 1


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _loadMarkerViewModule(currentRealm='RU'):
    nativeMarkers = []
    callbacks = []

    def createNativeMarker():
        marker = FakeNativeMarker()
        nativeMarkers.append(marker)
        return marker

    _module('BigWorld',
            callback=lambda delay, function:
            callbacks.append((delay, function)) or len(callbacks),
            testCallbacks=callbacks)
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
    def test_layout_bridge_cache_stats_and_reset(self):
        markerView, _ = _loadMarkerViewModule()
        flash = FakeFlash()
        view = object.__new__(markerView.MarkerOverlayView)
        view._ready = True
        view._controller = None
        view._nativeMarkers = {}
        view._layoutMarkers = {}
        view.flashObject = flash
        view._initializeLayoutSolver()

        def box(left, top, right, bottom):
            corners = [[left, top], [right, top], [right, bottom],
                       [left, bottom]]
            return ProxyList(corners + corners)

        payload = Bag(
            width=400.0, height=300.0,
            hull=box(120.0, 90.0, 280.0, 210.0),
            turret=box(160.0, 60.0, 240.0, 140.0),
            items=ProxyList([Bag(
                id='front', x=200.0, y=180.0,
                width=64.0, height=24.0, part='hull')]))

        first = view.solveLayout(payload)
        cached = view.solveLayout(payload)
        stats = view.getLayoutPerformanceStats()

        self.assertEqual(first['revision'], 1)
        self.assertEqual(cached, {'revision': 1})
        self.assertEqual(stats['cacheHits'], 1)
        self.assertEqual(stats['cacheMisses'], 1)
        self.assertEqual(stats['fullSearches'], 1)
        self.assertEqual(stats['stablePlanHits'], 0)
        self.assertEqual(stats['cachedCallbacks']['count'], 1)
        self.assertEqual(stats['changedSolves']['count'], 1)
        self.assertGreater(stats['candidateCount'], 0)

        view.clearMarkers()
        afterReset = view.solveLayout(payload)
        self.assertEqual(flash.cleared, 1)
        self.assertEqual(afterReset['revision'], 1)
        self.assertIn('placements', afterReset)

    def test_unexpected_layout_failure_is_disabled_once(self):
        markerView, _ = _loadMarkerViewModule()
        markerView.log.addHandler(logging.NullHandler())

        class BrokenSolver(object):
            revision = 7
            candidateCount = 0

            def solve(self, *args):
                raise RuntimeError('broken solver')

        disabled = []
        controller = Bag(setOption=lambda name, value:
                         disabled.append((name, value)))
        view = object.__new__(markerView.MarkerOverlayView)
        view._controller = controller
        view._initializeLayoutSolver()
        view._layoutSolver = BrokenSolver()
        corners = ProxyList([[0.0, 0.0], [100.0, 0.0],
                             [100.0, 100.0], [0.0, 100.0]] * 2)
        payload = Bag(width=200.0, height=200.0, hull=corners,
                      turret=corners, items=ProxyList([]))

        first = view.solveLayout(payload)
        second = view.solveLayout(payload)
        callbacks = sys.modules['BigWorld'].testCallbacks

        self.assertEqual(first, {'revision': 7, 'disabled': True})
        self.assertEqual(second, {'revision': 7, 'disabled': True})
        self.assertEqual(len(callbacks), 1)
        callbacks[0][1]()
        self.assertEqual(disabled, [('showUiPoints', False)])

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
