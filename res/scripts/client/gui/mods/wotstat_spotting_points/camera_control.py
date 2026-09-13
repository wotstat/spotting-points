_MOVEMENT_STATE_ATTRIBUTES = (
    ('_HangarCameraSystem__rotationEnabled',
     '_HangarCameraSystem__zoomEnabled'),
    ('_HangarCameraManager__rotationEnabled',
     '_HangarCameraManager__zoomEnabled'),
)


def _getCameraMovementState(cameraManager):
    for rotationAttribute, zoomAttribute in _MOVEMENT_STATE_ATTRIBUTES:
        if (hasattr(cameraManager, rotationAttribute)
                and hasattr(cameraManager, zoomAttribute)):
            return (bool(getattr(cameraManager, rotationAttribute)),
                    bool(getattr(cameraManager, zoomAttribute)))
    return None


def disableCameraRotation(cameraManager):
    movementState = _getCameraMovementState(cameraManager)
    if movementState is None:
        return None
    cameraManager.enableMovementByMouse(False, movementState[1])
    return movementState


def restoreCameraMovement(cameraManager, movementState):
    if cameraManager is not None and movementState is not None:
        cameraManager.enableMovementByMouse(*movementState)
