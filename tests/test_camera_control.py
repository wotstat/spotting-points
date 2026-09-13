import importlib
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'res',
                              'scripts', 'client', 'gui', 'mods'))


class HangarCameraSystem(object):
    def __init__(self, rotationEnabled, zoomEnabled):
        self.__rotationEnabled = rotationEnabled
        self.__zoomEnabled = zoomEnabled

    def enableMovementByMouse(self, enableRotation=True, enableZoom=True):
        self.__rotationEnabled = enableRotation
        self.__zoomEnabled = enableZoom

    def movementState(self):
        return self.__rotationEnabled, self.__zoomEnabled


class HangarCameraManager(object):
    def __init__(self, rotationEnabled, zoomEnabled):
        self.__rotationEnabled = rotationEnabled
        self.__zoomEnabled = zoomEnabled

    def enableMovementByMouse(self, enableRotation=True, enableZoom=True):
        self.__rotationEnabled = enableRotation
        self.__zoomEnabled = enableZoom

    def movementState(self):
        return self.__rotationEnabled, self.__zoomEnabled


def _loadCameraControl():
    try:
        return importlib.import_module(
            'wotstat_spotting_points.camera_control')
    except ImportError:
        return None


def _missing(*args):
    return None


class CameraControlTests(unittest.TestCase):
    def test_disable_rotation_preserves_zoom_for_both_clients(self):
        cameraControl = _loadCameraControl()
        disableCameraRotation = getattr(
            cameraControl, 'disableCameraRotation', _missing)

        wgCamera = HangarCameraSystem(True, False)
        lestaCamera = HangarCameraManager(True, True)

        self.assertEqual(disableCameraRotation(wgCamera), (True, False))
        self.assertEqual(wgCamera.movementState(), (False, False))
        self.assertEqual(disableCameraRotation(lestaCamera), (True, True))
        self.assertEqual(lestaCamera.movementState(), (False, True))

    def test_restore_movement_uses_the_exact_saved_state(self):
        cameraControl = _loadCameraControl()
        restoreCameraMovement = getattr(
            cameraControl, 'restoreCameraMovement', _missing)
        camera = HangarCameraSystem(False, True)

        camera.enableMovementByMouse(False, False)
        restoreCameraMovement(camera, (False, True))

        self.assertEqual(camera.movementState(), (False, True))


if __name__ == '__main__':
    unittest.main()
