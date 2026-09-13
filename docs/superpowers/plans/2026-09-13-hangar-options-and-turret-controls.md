# Hangar Options and Turret Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact non-modal settings window opened from ModsList, three independent visualization switches, and descriptor-limited mouse control of the hangar turret and gun.

**Architecture:** Python owns an in-memory options model, rendering, and hangar input lifecycle. A unique Scaleform `AbstractWindowView` SWF displays stock checkboxes and forwards changes to Python. Turret dragging uses the native cursor ray and collision query plus descriptor limit helpers, with a fixed direction and 0.003-radian-per-pixel sensitivity, while an EventBus restriction suppresses camera movement only during an accepted turret/gun drag.

**Tech Stack:** Python 2.7, BigWorld hangar APIs, Scaleform/AS3, Apache Royale 0.9.12, Python `unittest`, PowerShell packaging, WotStat REPL 1.4.1 MCP.

**Spec:** `docs/superpowers/specs/2026-09-13-hangar-options-and-turret-controls-design.md`

## Global Constraints

- Use ModsList only; do not import or register with ModsSettings API.
- All four options initialize to `False` on every client start and are never written to disk.
- Register a unique SWF on `WindowLayer.WINDOW` with `isModal=False`; do not replace stock or third-party resources.
- Do not monkey-patch `LobbyView`, `game.handleMouseEvent`, or another mod's code.
- Support MT 1.45 and WoT 2.x contracts confirmed in `E:/wot-mods/wot-src-ru` and `E:/wot-mods/wot-src-eu`.
- Use `C:/Users/soprachev/Desktop/wotstat-repl_1.4.1.exe` through its MCP tools for runtime validation; restart it only if MCP becomes unavailable or hangs.
- Keep AS3 dependency SWCs local and Git-ignored; package only the compiled unique SWF.

---

### Task 1: In-memory options and pure rotation math

**Files:**
- Create: `res/scripts/client/gui/mods/wotstat_spotting_points/options.py`
- Create: `res/scripts/client/gui/mods/wotstat_spotting_points/rotation_math.py`
- Create: `tests/test_options.py`
- Create: `tests/test_rotation_math.py`

**Interfaces:**
- Produces: `DisplayOptions()` with boolean attributes `showMaskPoints`, `showSpotPoints`, `showGuides`, `allowTurretRotation`, `setValue(name, value) -> bool`, `asDict() -> dict`, and `hasVisuals() -> bool`.
- Produces: `nextAngles(yaw, pitch, dx, dy, yawLimits, pitchLimits, sensitivity=0.003) -> (yaw, pitch)`.
- Consumes: no game-client imports, so both units run under stock Python 2.7 tests.

- [ ] **Step 1: Write failing options tests**

```python
class DisplayOptionsTests(unittest.TestCase):
    def test_defaults_are_all_disabled(self):
        options = DisplayOptions()
        self.assertEqual(options.asDict(), {
            'showMaskPoints': False,
            'showSpotPoints': False,
            'showGuides': False,
            'allowTurretRotation': False,
        })
        self.assertFalse(options.hasVisuals())

    def test_visual_and_rotation_updates_are_independent(self):
        options = DisplayOptions()
        self.assertTrue(options.setValue('showSpotPoints', True))
        self.assertTrue(options.showSpotPoints)
        self.assertTrue(options.hasVisuals())
        self.assertTrue(options.setValue('allowTurretRotation', True))
        self.assertFalse(options.setValue('unknown', True))
```

- [ ] **Step 2: Run options tests and verify RED**

Run: `C:/Python27/python.exe -B -m unittest tests.test_options`

Expected: FAIL because `wotstat_spotting_points.options` does not exist.

- [ ] **Step 3: Implement the options model**

```python
OPTION_NAMES = ('showMaskPoints', 'showSpotPoints', 'showGuides',
                'allowTurretRotation')

class DisplayOptions(object):
    def __init__(self):
        for name in OPTION_NAMES:
            setattr(self, name, False)

    def setValue(self, name, value):
        if name not in OPTION_NAMES:
            return False
        setattr(self, name, bool(value))
        return True

    def asDict(self):
        return dict((name, getattr(self, name)) for name in OPTION_NAMES)

    def hasVisuals(self):
        return self.showMaskPoints or self.showSpotPoints or self.showGuides
```

- [ ] **Step 4: Write failing rotation tests**

```python
class RotationMathTests(unittest.TestCase):
def test_full_circle_yaw_is_normalized(self):
    yaw, pitch = nextAngles(math.pi - 0.01, 0.0, -100.0, 0.0,
                            None, (-0.2, 0.3))
    self.assertTrue(0.0 <= yaw < 2.0 * math.pi)
        self.assertEqual(pitch, 0.0)

    def test_limited_yaw_and_pitch_are_clamped(self):
        yaw, pitch = nextAngles(0.0, 0.0, -1000.0, 1000.0,
                                (-0.4, 0.5), (-0.1, 0.2))
        self.assertEqual((yaw, pitch), (0.5, 0.2))
```

- [ ] **Step 5: Run rotation tests and verify RED**

Run: `C:/Python27/python.exe -B -m unittest tests.test_rotation_math`

Expected: FAIL because `wotstat_spotting_points.rotation_math` does not exist.

- [ ] **Step 6: Implement pure angle updates**

```python
def clamp(value, limits):
    return max(limits[0], min(limits[1], value))

def normalizeAngle(value):
    return value % (2.0 * math.pi)

def nextAngles(yaw, pitch, dx, dy, yawLimits, pitchLimits,
               sensitivity=0.003):
    yaw -= dx * sensitivity
    yaw = normalizeAngle(yaw) if yawLimits is None else clamp(yaw, yawLimits)
    pitch = clamp(pitch + dy * sensitivity, pitchLimits)
    return yaw, pitch
```

- [ ] **Step 7: Run both focused tests and commit**

Run: `C:/Python27/python.exe -B -m unittest tests.test_options tests.test_rotation_math`

Expected: 4 tests PASS.

Commit:

```powershell
git add res/scripts/client/gui/mods/wotstat_spotting_points/options.py res/scripts/client/gui/mods/wotstat_spotting_points/rotation_math.py tests/test_options.py tests/test_rotation_math.py
git commit -m "feat: add transient display and rotation state"
```

### Task 2: Independent visualization switches and moving gun point

**Files:**
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/geometry.py`
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/renderer.py`
- Modify: `tests/test_geometry.py`

**Interfaces:**
- Consumes: three booleans from `DisplayOptions`.
- Produces: `replacePoint(points, index, point) -> list` and `drawVehicle(vehicle, showMaskPoints, showSpotPoints, showGuides)`.
- Preserves: `getWorldGeometry(vehicle) -> (maskPoints, spotPoints, lines)`.

- [ ] **Step 1: Add the failing live-point replacement test**

```python
def test_replace_point_does_not_leave_static_duplicate(self):
    from wotstat_spotting_points.geometry import replacePoint
    original = ['rear', 'front', 'left', 'right', 'static-gun', 'top']
    replaced = replacePoint(original, 4, 'moving-gun')
    self.assertEqual(replaced, ['rear', 'front', 'left', 'right',
                                'moving-gun', 'top'])
    self.assertEqual(original[4], 'static-gun')
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `C:/Python27/python.exe -B -m unittest tests.test_geometry.GeometryTests.test_replace_point_does_not_leave_static_duplicate`

Expected: FAIL because `replacePoint` is not defined.

- [ ] **Step 3: Add the helper and update world geometry**

```python
def replacePoint(points, index, point):
    result = list(points)
    result[index] = point
    return result
```

After converting the six static mask points, replace index 4 with the live
`TankNodeNames.GUN_JOINT` position instead of appending it. Build observation
points as `[maskPoints[5], maskPoints[4]]`.

- [ ] **Step 4: Gate each primitive group in `drawVehicle`**

```python
def drawVehicle(vehicle, showMaskPoints, showSpotPoints, showGuides):
    maskPoints, spotPoints, lines = getWorldGeometry(vehicle)
    if showGuides:
        for line in lines:
            drawLine(drawer, line)
    if showMaskPoints:
        for point in maskPoints:
            shared = showSpotPoints and isShared(point, spotPoints)
            if not shared:
                drawSphere(drawer, point, 0.05, MASK_COLORS)
    if showSpotPoints:
        for point in spotPoints:
            drawSphere(drawer, point, 0.05, SPOT_COLORS)
```

- [ ] **Step 5: Run geometry regression tests and commit**

Run: `C:/Python27/python.exe -B -m unittest tests.test_geometry`

Expected: all geometry tests PASS, including the new replacement regression.

Commit:

```powershell
git add res/scripts/client/gui/mods/wotstat_spotting_points/geometry.py res/scripts/client/gui/mods/wotstat_spotting_points/renderer.py tests/test_geometry.py
git commit -m "feat: control spotting visuals independently"
```

### Task 3: Conflict-minimal turret drag controller

**Files:**
- Create: `res/scripts/client/gui/mods/wotstat_spotting_points/turret_control.py`
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/controller.py`
- Modify: `tests/test_rotation_math.py`

**Interfaces:**
- Consumes: `nextAngles`, `IHangarSpace`, `CameraRelatedEvents.LOBBY_VIEW_MOUSE_MOVE`, `CollisionComponent.collideAllWorld`, `calcPitchLimitsFromDesc`, `ITurretAndGunAngles.set`.
- Produces: `TurretMouseControl.setEnabled(enabled)`, `cancelDrag()`, `destroy()` and an EventBus restriction returning `False` only during an accepted drag.
- Controller produces: `setOption(name, value) -> bool` and `getOptions() -> dict` for the UI bridge.

- [ ] **Step 1: Add failing math cases for unchanged axes**

```python
def test_zero_delta_keeps_angles(self):
    self.assertEqual(nextAngles(0.2, -0.1, 0.0, 0.0,
                                (-0.5, 0.5), (-0.2, 0.3)),
                     (0.2, -0.1))
```

- [ ] **Step 2: Run the focused test and verify RED or incomplete behavior**

Run: `C:/Python27/python.exe -B -m unittest tests.test_rotation_math`

Expected: PASS only if the Task 1 implementation already preserves zero deltas; otherwise FAIL and fix `nextAngles` before game integration.

- [ ] **Step 3: Implement hit detection using the native armor-inspector path**

```python
cursor = GUI.mcursor().position
ray, start = cameras.getWorldRayAndPoint(cursor.x, cursor.y)
ray.normalise()
hits = appearance.collisions.collideAllWorld(
    start, start + ray.scale(BigWorld.projection().farPlane))
for hit in hits:
    partName = appearance.collisions.getPartName(hit[3])
    return partName in (TankPartNames.TURRET, TankPartNames.GUN)
return False
```

Require `hangar.spaceInited`, `hangar.isCursorOver3DScene`, a loaded selectable
vehicle, and a valid appearance before the query. The nearest reported vehicle
part decides whether drag starts.

- [ ] **Step 4: Implement drag lifecycle and selective restriction**

Subscribe to `hangar.onMouseDown`, `hangar.onMouseUp`, and
`hangar.onVehicleChangeStarted` only while enabled. Add the EventBus restriction
at `EventPriority.HIGH` only after an accepted mouse-down, and remove it on
mouse-up/cancel. In the restriction, call `_rotate(event.ctx)` and return
`False`; otherwise return `True`.

- [ ] **Step 5: Apply client descriptor limits and both appearance contracts**

Calculate the yaw-dependent pitch interval with:

```python
pitchLimits = calcPitchLimitsFromDesc(
    yaw, descriptor.gun.pitchLimits,
    descriptor.hull.turretPitches[0],
    descriptor.turret.gunJointPitch)
```

Pass that interval and `descriptor.gun.turretYawLimits` into `nextAngles`.
Do not change yaw when `gun.staticTurretYaw is not None`, and do not change pitch
when `gun.staticPitch is not None`. Call `turretRotator.start(yaw, 0.0)`. For
pitch, call `appearance.rotateGunForAngle(pitch)` when available; otherwise set
the `TankNodeNames.GUN_INCLINATION`/`TankPartNames.GUN` node's `local` rotation
matrix. Finally call `ITurretAndGunAngles.set(gunPitch=pitch, turretYaw=yaw)`.

- [ ] **Step 6: Replace the controller's single toggle with options**

Create one `DisplayOptions` and one `TurretMouseControl`. `setOption` validates
the key, starts/stops the frame callback based on `hasVisuals()`, and forwards
`allowTurretRotation` to the mouse controller. `_draw` passes the three visual
booleans to `drawVehicle`. `destroy` disables both paths and unsubscribes.

- [ ] **Step 7: Run all Python tests and commit**

Run: `C:/Python27/python.exe -B -m unittest discover -s tests`

Expected: all tests PASS.

Commit:

```powershell
git add res/scripts/client/gui/mods/wotstat_spotting_points/turret_control.py res/scripts/client/gui/mods/wotstat_spotting_points/controller.py tests/test_rotation_math.py
git commit -m "feat: rotate hangar turret with scoped mouse drag"
```

### Task 4: Compact native Scaleform settings window

**Files:**
- Create: `as3/src/wotstat/spottingpoints/SettingsWindow.as`
- Create: `as3/asconfig.json`
- Create: `as3/libs/README.md`
- Modify: `.gitignore`
- Create: `res/scripts/client/gui/mods/wotstat_spotting_points/settings_view.py`

**Interfaces:**
- AS3 consumes: `as_setData(options:Object, labels:Object)` from Python.
- AS3 produces DAAPI callbacks: `optionChanged(name:String, value:Boolean)` and `onWindowClose()`.
- Python produces: `registerSettingsView()`, `unregisterSettingsView()`, `showSettings(controller)` and `SettingsWindow(AbstractWindowView)`.

- [ ] **Step 1: Add the AS3 source and use stock controls**

Create a `SettingsWindow` extending `AbstractWindowView`, sized about 420×190.
In `onPopulate`, set `window.title`, create four `CheckBox` instances through
`App.utils.classFactory.getComponent('CheckBox', CheckBox)`, position them in a
single column, register `ButtonEvent.CLICK`, and reveal the view. Set each label
and `selected` value from `as_setData`. On click, call
`optionChanged(checkBox.name, checkBox.selected)`. Dispose listeners and controls
in `onBeforeDispose`/`onDispose`.

- [ ] **Step 2: Add the Python view bridge and uniqueness guard**

Register:

```python
ViewSettings(VIEW_ALIAS, SettingsWindow, VIEW_SWF,
             WindowLayer.WINDOW, None, ScopeTemplates.DEFAULT_SCOPE,
             isModal=False, canDrag=True, canClose=True, isCentered=True)
```

`showSettings(controller)` uses `ViewKey(VIEW_ALIAS)` to find an existing view;
if absent, stores the controller for construction and calls
`app.loadView(SFViewLoadParams(VIEW_ALIAS))`. `_populate` sends
`controller.getOptions()` and Russian labels. `optionChanged` calls
`controller.setOption(str(name), bool(value))`. `onWindowClose` destroys only
the view, preserving controller state.

- [ ] **Step 3: Configure local SWCs without committing them**

Ignore `as3/libs/*.swc` while retaining `as3/libs/README.md`. The README lists
the required `gui_base`, `base_app`, `common`, `common_i18n_library`, and
`playerglobal` libraries and says they must come from the developer's local
client/toolchain. For this workspace, copy the already available local SWCs from
`E:/wot-mods/wotstat-map-viewer-mod/as3/libs` into the ignored directory.

- [ ] **Step 4: Compile the SWF directly as a RED/GREEN integration check**

Run the Royale `mxmlc.bat` command with target player 17, SWF version 17, source
path `as3/src`, external library path `as3/libs`, and output
`.build/res/gui/flash/wotstatSpottingPointsSettings.swf`.

Expected first result: any wrong linkage/import fails with a compiler error.
Correct the source until compilation succeeds without warnings that change
runtime behavior.

- [ ] **Step 5: Commit the window sources and bridge**

```powershell
git add .gitignore as3/asconfig.json as3/libs/README.md as3/src/wotstat/spottingpoints/SettingsWindow.as res/scripts/client/gui/mods/wotstat_spotting_points/settings_view.py
git commit -m "feat: add non-modal spotting settings window"
```

### Task 5: Bootstrap, build, packaging, and documentation

**Files:**
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/bootstrap.py`
- Modify: `build.ps1`
- Modify: `README.md`
- Modify: `docs/design.md`
- Modify: `docs/plan.md`

**Interfaces:**
- Consumes: `registerSettingsView`, `unregisterSettingsView`, `showSettings`.
- Produces: ModsList callback opening the unique settings view and release archives containing `res/gui/flash/wotstatSpottingPointsSettings.swf`.

- [ ] **Step 1: Change bootstrap to open the custom view**

During `init`, construct the controller, register the view, then add a ModsList
entry named `Настройки габаритных и обзорных точек` whose callback is
`lambda: showSettings(instance)`. If either registration fails, remove anything
already registered and destroy the controller. During `fini`, destroy the view,
unregister it, remove the ModsList entry, and destroy the controller
idempotently.

- [ ] **Step 2: Extend the existing linear build**

Before Python packaging, create `.build/res/gui/flash` and compile
`SettingsWindow.as` there using the configurable `$Royale` and `$JavaHome`
parameters. Preserve the current staging copy, Python 2.7 compilation, and dual
ZIP_STORED package generation.

- [ ] **Step 3: Update user and developer documentation**

Document the four defaults, immediate in-session behavior, ModsList-to-window
flow, non-persistence, turret/gun drag rules, unique SWF, ModsList dependency,
AS3 toolchain, and MCP runtime verification. Remove statements describing the
old single toggle or a Python-only build.

- [ ] **Step 4: Run unit tests and release build**

Run:

```powershell
C:/Python27/python.exe -B -m unittest discover -s tests
./build.ps1 -Version 0.2.0 -Python C:/Python27/python.exe
```

Expected: all tests PASS; both `dist/wotstat.spotting-points_0.2.0.mtmod` and
`dist/wotstat.spotting-points_0.2.0.wotmod` are produced.

- [ ] **Step 5: Inspect archives and repository cleanliness**

List both archives and verify they contain compiled Python plus exactly one
unique `res/gui/flash/wotstatSpottingPointsSettings.swf`, contain no `.py`,
`.as`, `.swc`, or stock-overriding path, and have matching file sets. Run
`git diff --check` and confirm no build outputs are tracked.

- [ ] **Step 6: Commit integration and docs**

```powershell
git add res/scripts/client/gui/mods/wotstat_spotting_points/bootstrap.py build.ps1 README.md docs/design.md docs/plan.md
git commit -m "feat: open spotting controls from ModsList"
```

### Task 6: MT runtime validation through WotStat REPL MCP

**Files:**
- Modify only if a concrete runtime failure requires a tested correction.

**Interfaces:**
- Consumes: `dist/wotstat.spotting-points_0.2.0.mtmod` and the WotStat REPL MCP tools.
- Produces: runtime evidence for UI, rendering, drag targeting, limits, cleanup, and fresh-start defaults.

- [ ] **Step 1: Confirm MCP client capabilities**

Call `wot_list_clients` and verify `E:/Games/Tanki` reports agent 1.4.1 with
`repl`, `input`, and `screenshot`. If the MCP server is unavailable or hangs,
restart `C:/Users/soprachev/Desktop/wotstat-repl_1.4.1.exe`, then call
`wot_list_clients` again.

- [ ] **Step 2: Install and load the exact release package**

Gracefully close the active MT client through MCP, copy the 0.2.0 package into
`E:/Games/Tanki/mods/1.45.0.0`, remove only the older package for this same mod
ID after verifying its exact path, and restart the client through MCP. Use
`wot_exec` to print the loaded module version and option dictionary.

- [ ] **Step 3: Verify the window and independent visual switches**

Use MCP mouse input to open ModsList and the mod entry. Capture a screenshot of
the small window over the interactive hangar. Toggle each visual option and
capture/check screenshots showing mask-only, spot-only, guides-only, and all-off
states. Close and reopen the window and verify the current in-session values are
unchanged.

- [ ] **Step 4: Verify input routing and descriptor limits**

Enable turret rotation. Use MCP mouse input to drag the hull/empty scene and
verify normal camera movement. Drag the turret/gun and verify yaw and pitch
change while the camera does not. Use `wot_exec` to read the applied angles and
descriptor limits, drive beyond both axes, and verify clamping. Confirm the live
combined gun point follows the gun and the guides do not rotate.

- [ ] **Step 5: Verify restart defaults and logs**

Restart once more through MCP, open the settings window, and confirm all four
checkboxes are off. Read only the relevant recent log interval and verify there
are no mod exceptions, duplicate listeners, callbacks, or restrictions.

- [ ] **Step 6: Run final fresh verification and commit any runtime fixes**

After any correction, repeat its failing test first, rebuild 0.2.0, reinstall,
and repeat the affected MCP scenario. Finish with:

```powershell
C:/Python27/python.exe -B -m unittest discover -s tests
./build.ps1 -Version 0.2.0 -Python C:/Python27/python.exe
git diff --check
git status --short
```

Expected: tests and build succeed, runtime checks pass, and Git shows only the
intended committed source history.
