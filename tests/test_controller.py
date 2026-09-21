import importlib
import logging
import os
import sys
import types
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class FakeSelectableVehicle(object):
    isVehicleLoaded = True
    appearance = object()
    typeDescriptor = object()


class Bag(object):
    def __init__(self, **attributes):
        self.__dict__.update(attributes)


class FakeHangar(object):
    def __init__(self, vehicle=None, cursorOverScene=True):
        self.spaceInited = True
        self.isCursorOver3DScene = cursorOverScene
        self.vehicle = vehicle

    def getVehicleEntity(self):
        return self.vehicle


class FakeMarkerView(object):
    def __init__(self, hit='front'):
        self.clears = 0
        self.hit = hit
        self.hitCalls = 0
        self.tooltipClears = 0
        self.layoutDebug = []
        self.calloutModes = []
        self.tooltipsEnabled = []
        self.updates = []

    def clearMarkers(self):
        self.clears += 1

    def hitTest(self, x, y):
        self.hitCalls += 1
        return self.hit

    def clearTooltipHover(self):
        self.tooltipClears += 1

    def setLayoutDebug(self, value):
        self.layoutDebug.append(value)

    def setCalloutMode(self, value):
        self.calloutModes.append(value)

    def setTooltipsEnabled(self, value):
        self.tooltipsEnabled.append(value)

    def updateSceneActive(self):
        return True

    def updateMarkers(self, *args):
        self.updates.append(args)


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _loadControllerModule():
    callbacks = []
    _module('BigWorld', callback=lambda delay, fn: callbacks.append(delay) or 1,
            cancelCallback=lambda callbackId: None,
            camera=lambda: Bag(position=(0, 0, 0)),
            time=lambda: 0.0)
    _module('GUI', mcursor=lambda: Bag(
        position=Bag(x=0.0, y=0.0), inWindow=True, inFocus=True))
    _module('AvatarInputHandler')
    _module('AvatarInputHandler.cameras',
            getViewProjectionMatrix=lambda: None)
    _module('ClientSelectableCameraVehicle',
            ClientSelectableCameraVehicle=FakeSelectableVehicle)
    _module('Math', Matrix=object, Vector4=object)
    _module('helpers', dependency=Bag(instance=lambda cls: None))
    _module('skeletons')
    _module('skeletons.gui')
    _module('skeletons.gui.shared')
    _module('skeletons.gui.shared.utils', IHangarSpace=object)
    _module('wotstat_spotting_points.marker_view',
            hideMarkerView=lambda controller=None: None,
            showMarkerView=lambda controller: True)
    _module('wotstat_spotting_points.settings_view',
            updateDisplayedOptions=lambda options: None)
    _module('wotstat_spotting_points.renderer',
            drawVehicle=lambda vehicle, *args: ('geometry',),
            drawGeometry=lambda geometry, *args: None,
            getLayoutBounds=lambda vehicle: None,
            getWorldGeometry=lambda vehicle, includeLines=True,
            includeGunCircle=False: ('geometry',))
    _module('wotstat_spotting_points.turret_control',
            TurretMouseControl=object)
    sys.modules.pop('wotstat_spotting_points.controller', None)
    return importlib.import_module('wotstat_spotting_points.controller'), callbacks


class ControllerLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controllerModule, cls.callbacks = _loadControllerModule()
        cls.controllerModule.log.addHandler(logging.NullHandler())

    def makeController(self, vehicle=None, cursorOverScene=True):
        from wotstat_spotting_points.options import DisplayOptions
        controller = object.__new__(
            self.controllerModule.SpottingPointsController)
        controller.options = DisplayOptions()
        controller._callbackId = None
        controller._hangar = FakeHangar(vehicle, cursorOverScene)
        controller._markerView = FakeMarkerView()
        controller._hoveredPointId = 'front'
        controller._nextMarkerUpdate = 0.0
        return controller

    def test_invalid_vehicle_clears_persistent_markers(self):
        controller = self.makeController()
        controller.options.showUiPoints = True

        controller._draw()

        self.assertEqual(controller._markerView.clears, 1)
        self.assertIsNone(controller._hoveredPointId)

    def test_missing_vehicle_geometry_clears_persistent_markers(self):
        controller = self.makeController(FakeSelectableVehicle())
        controller.options.showUiPoints = True
        original = self.controllerModule.getWorldGeometry
        self.controllerModule.getWorldGeometry = lambda *args: None
        try:
            controller._draw()
        finally:
            self.controllerModule.getWorldGeometry = original

        self.assertEqual(controller._markerView.clears, 1)
        self.assertIsNone(controller._hoveredPointId)

    def test_marker_failure_disables_only_ui_points(self):
        controller = self.makeController(FakeSelectableVehicle())
        for name in ('showMaskPoints', 'showSpotPoints', 'showUiPoints',
                     'showGuides'):
            setattr(controller.options, name, True)

        def fail(*args):
            raise RuntimeError('marker bridge failed')

        controller._updateMarkerView = fail
        controller._draw()

        self.assertFalse(controller.options.showUiPoints)
        self.assertTrue(controller.options.showMaskPoints)
        self.assertTrue(controller.options.showSpotPoints)
        self.assertTrue(controller.options.showGuides)

    def test_ui_hover_is_not_blocked_by_the_hangar_3d_scene_gate(self):
        controller = self.makeController(cursorOverScene=False)

        controller._updateMarkerHover(True)

        self.assertEqual(controller._hoveredPointId, 'front')
        self.assertEqual(controller._markerView.hitCalls, 1)

    def test_hover_is_skipped_when_the_marker_scene_is_inactive(self):
        controller = self.makeController(cursorOverScene=False)

        controller._updateMarkerHover(False)

        self.assertIsNone(controller._hoveredPointId)
        self.assertEqual(controller._markerView.hitCalls, 0)
        self.assertEqual(controller._markerView.tooltipClears, 1)

    def test_tooltip_option_is_applied_to_active_and_new_views(self):
        controller = self.makeController()
        view = controller._markerView

        self.assertTrue(controller.setOption('showTooltips', False))
        self.assertEqual(view.tooltipsEnabled, [False])
        self.assertEqual(controller._hoveredPointId, 'front')

        controller.attachMarkerView(view)
        self.assertEqual(view.calloutModes, [0])
        self.assertEqual(view.tooltipsEnabled, [False, False])

    def test_active_hover_geometry_is_forwarded_to_the_ui_overlay(self):
        vehicle = FakeSelectableVehicle()
        controller = self.makeController(vehicle)
        highlight = Bag(faded=['face'], bright=['guide'])
        maskPoints = [(index, 0, 0) for index in range(7)]
        spotPoints = [maskPoints[5], maskPoints[6]]
        geometry = (maskPoints, spotPoints, [], {'front': highlight})

        try:
            controller._updateMarkerView(vehicle, geometry)
        except ValueError as error:
            self.fail('world geometry has no UI highlight channel: %s' % error)

        self.assertEqual(len(controller._markerView.updates), 1)
        self.assertIs(controller._markerView.updates[0][-1], highlight)

    def test_full_gun_circle_is_requested_only_for_moving_gun_hover(self):
        vehicle = FakeSelectableVehicle()
        controller = self.makeController(vehicle)
        controller.options.showUiPoints = True
        controller._hoveredPointId = 'gunMoving'
        calls = []
        original = self.controllerModule.getWorldGeometry
        self.controllerModule.getWorldGeometry = (
            lambda *args: calls.append(args) or ('geometry',))
        controller._updateMarkerView = lambda *args: None
        try:
            controller._draw()
        finally:
            self.controllerModule.getWorldGeometry = original

        self.assertEqual(calls, [(vehicle, True, True)])

    def test_ui_hover_waits_for_marker_gate_before_building_guides(self):
        vehicle = FakeSelectableVehicle()
        controller = self.makeController(vehicle)
        controller.options.showUiPoints = True
        controller._hoveredPointId = 'gunMoving'
        controller._nextMarkerUpdate = 1.0
        calls = []
        original = self.controllerModule.getWorldGeometry
        self.controllerModule.getWorldGeometry = (
            lambda *args: calls.append(args) or ('geometry',))
        try:
            controller._draw()
        finally:
            self.controllerModule.getWorldGeometry = original

        self.assertEqual(calls, [(vehicle, False, False)])
        self.assertAlmostEqual(self.callbacks[-1], 1.0 / 30.0)

    def test_layout_debug_option_updates_the_attached_overlay(self):
        controller = self.makeController()

        self.assertTrue(controller.setOption('layoutDebug', True))

        self.assertTrue(controller.options.layoutDebug)
        self.assertEqual(controller._markerView.layoutDebug, [True])


if __name__ == '__main__':
    unittest.main()
