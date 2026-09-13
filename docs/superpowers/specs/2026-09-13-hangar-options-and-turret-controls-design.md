# Hangar options and turret controls

## Goal

Replace the current one-click display toggle with a small, native-looking,
non-modal hangar window opened by the existing ModsList entry. The window
controls the visibility of mask points, observation points, guides, and the
ability to rotate the selected tank's turret and gun by dragging them.

This feature uses ModsList only. It does not register with ModsSettings API,
open the ModsSettings screen, replace game resources, or persist settings.

## User experience

The ModsList entry is renamed to a neutral settings action and opens one
instance of the mod window. If that instance is already open, a second copy is
not created. The window uses the standard `AbstractWindowView` frame and stock
checkbox controls, is draggable and closable, and is registered on
`WindowLayer.WINDOW` with `isModal=False`. Empty hangar space therefore remains
interactive while the window is open.

The window contains four checkboxes:

1. `Отображать габаритные точки`
2. `Отображать обзорные точки`
3. `Отображать направляющие`
4. `Разрешить вращение башни мышью`

All values are `False` when the mod initializes. Changes take effect
immediately. Closing and reopening the window keeps the current in-memory
values, while restarting the client resets all four values to `False`.

## UI architecture

A uniquely named SWF owned by the mod implements the small window. It creates
the native checkbox controls through the game's component factory rather than
shipping copied skins. A minimal Python `AbstractWindowView` bridge supplies
the current state and forwards checkbox changes to the controller.

The bootstrap remains the sole integration point. It registers the custom view
and the ModsList entry during `init`, opens the view from the ModsList callback,
and removes both registrations during `fini`. Repeated `init` and `fini` calls
remain safe.

No existing game or third-party functions are replaced for the window. The
AS3 compiler uses locally supplied game SWCs, which are ignored by Git and are
not added to the package; only the compiled, uniquely named SWF is packaged.

## Runtime state and rendering

The controller owns an in-memory state object with the four booleans. Rendering
runs only while at least one of the three visual options is enabled. The
renderer receives the three visibility flags and submits only the requested
primitives:

- mask points use the existing red two-pass spheres;
- observation points use the existing blue two-pass spheres;
- guides use the existing white/gray lines;
- a point enabled in both groups is drawn once in blue.

The live gun-joint position replaces the static gun mask point. Consequently,
the combined gun observation/mask point follows turret yaw and gun pitch without
leaving a stale red point behind. The top observation point remains attached to
the hull. Guide geometry continues to use the unrotated vehicle-local reference
geometry, so it does not follow turret rotation.

## Turret drag behavior

When mouse rotation is disabled, the mod has no effect on hangar input. When it
is enabled, the controller listens to the existing `IHangarSpace` mouse-down and
mouse-up events. On mouse-down it starts a turret drag only when the cursor is
over the 3D scene and the vehicle collision query reports the turret or gun as
the hit part. The query follows the native armor-inspector approach:
`GUI.mcursor()` plus `AvatarInputHandler.cameras.getWorldRayAndPoint`, then the
vehicle collision component. A drag beginning on the hull or empty hangar keeps
the normal camera behavior.

During an active turret drag, a high-priority EventBus restriction consumes
only `CameraRelatedEvents.LOBBY_VIEW_MOUSE_MOVE`. A turret or gun hit applies
`dx` to turret yaw and `dy` to gun pitch for every movable axis. Direction
does not depend on the hit side: moving the mouse right always decreases yaw,
which turns the turret counterclockwise. Both axes use a sensitivity of 0.003
radians per pixel. The restriction then returns `False` so the same movement
does not also rotate the camera. At every other time it returns `True`. This
avoids replacing `LobbyView.moveSpace`, the global input handler, or another
mod's listener.

Yaw uses `appearance.turretRotator.start(..., 0.0)`. Full-circle turrets use
the EU armor viewer's `[0, 2*pi)` range; limited-arc guns are clamped to
`gun.turretYawLimits`. Pitch is
clamped with `gun_rotation_shared.calcPitchLimitsFromDesc`, including the
current yaw, hull turret pitch, and gun-joint pitch. Vehicles with a static
turret or static gun keep that axis fixed. The public hangar turret/gun angle
service is updated together with the appearance so the selected angles survive
normal hangar model refreshes within the current client session.

The EU appearance exposes `rotateGunForAngle`; the MT appearance does not. A
small compatibility helper uses that method when present and otherwise writes
the same rotation matrix to the gun-inclination node using the MT node property.
Both paths are based on the corresponding local `wot-src` client contracts.

Mouse-up cancels an active drag and removes its EventBus restriction.
Disabling the option, vehicle replacement, hangar destruction, and mod teardown
also cancel the drag; disabling and teardown remove the input subscriptions.
All cleanup operations are idempotent.

## Failure handling and compatibility

If ModsList is unavailable, the mod logs one dependency error and does not
partially initialize. If the custom view cannot be registered, bootstrap rolls
back the controller and ModsList registration. A missing or not-yet-loaded
vehicle simply prevents drawing or drag start. An unexpected render or rotation
contract error stops the affected loop/drag and logs once instead of failing
every frame.

The package keeps unique Python and SWF paths and does not shadow stock files.
The implementation targets MT 1.45 and WoT 2.x using the checked local
`wot-src` trees. Runtime verification is performed on the available MT client;
WoT compatibility is source-verified unless a WoT client is also run.

## Verification

Pure Python 2.7 tests cover state defaults and updates, visual filtering, shared
point precedence, yaw normalization/clamping, pitch clamping inputs, and drag
state transitions that do not require client objects. Existing geometry tests
remain unchanged unless the live gun point replacement requires an explicit
regression assertion.

The release build must compile AS3 and Python, package both `.mtmod` and
`.wotmod`, and contain only unique mod resources. Runtime checks through the
WotStat REPL 1.4.1 MCP cover:

- ModsList opens one small non-modal window;
- the hangar camera still moves when dragging outside the window/turret;
- every checkbox updates its visual or input behavior immediately;
- all four options start disabled after client restart;
- a drag beginning on either the turret or gun changes yaw and pitch, moving
  right always turns counterclockwise, and a hull drag rotates the camera
  normally;
- yaw and pitch stop at the descriptor limits;
- the combined gun point follows the moved gun while guides remain fixed;
- closing/reopening the window keeps session state;
- teardown leaves no duplicate callbacks, listeners, restrictions, or errors.
