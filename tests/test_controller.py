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
        self.layoutDebug = []

    def clearMarkers(self):
        self.clears += 1

    def hitTest(self, x, y):
        self.hitCalls += 1
        return self.hit

    def setLayoutDebug(self, value):
        self.layoutDebug.append(value)


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
            getWorldGeometry=lambda vehicle, includeLines=True: ('geometry',))
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
        self.controllerModule.getWorldGeometry = lambda vehicle, lines: None
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

    def test_hover_is_skipped_outside_the_active_3d_scene(self):
        controller = self.makeController(cursorOverScene=False)

        controller._updateMarkerHover(True)

        self.assertIsNone(controller._hoveredPointId)
        self.assertEqual(controller._markerView.hitCalls, 0)

    def test_layout_debug_option_updates_the_attached_overlay(self):
        controller = self.makeController()

        self.assertTrue(controller.setOption('layoutDebug', True))

        self.assertTrue(controller.options.layoutDebug)
        self.assertEqual(controller._markerView.layoutDebug, [True])


if __name__ == '__main__':
    unittest.main()
