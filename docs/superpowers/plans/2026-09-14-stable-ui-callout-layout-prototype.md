# Stable UI Callout Layout Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a «Мир танков»-only prototype that lays UI point labels around separately projected hull and turret bounds with 45-degree leaders and stable motion.

**Architecture:** Reuse `GUI.HangarVehicleMarker` to project invisible hull and turret bounding-box corner anchors at render cadence. Keep the stateful screen-space solver in the marker SWF, where the projected positions are available every frame, while Python only supplies part-local corner geometry and native providers.

**Tech Stack:** Python 2.7, Scaleform/ActionScript 3, `GUI.HangarVehicleMarker`, Apache Royale 0.9.12, `unittest`, PowerShell.

**Spec:** `docs/superpowers/specs/2026-09-14-stable-ui-callout-layout-prototype-design.md`

## Global Constraints

- Target «Мир танков» (`mt-ru`) only.
- Keep existing point appearance, labels, hover behavior, and settings behavior.
- Do not add an AS3 headless test framework for this prototype.
- Do not replace game resources or global handlers.
- Do not close the game client after runtime validation.

---

### Task 1: Part-local projected-bound geometry

**Files:**
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/geometry.py`
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/renderer.py`
- Test: `tests/test_geometry.py`

**Interfaces:**
- Produces: `LayoutBounds(hull, turret)` where both fields contain eight part-local corner tuples.
- Produces: `getLayoutBounds(vehicle) -> LayoutBounds | None`.

- [ ] **Step 1: Write the failing corner test**

```python
def test_layout_bounds_keep_hull_and_turret_corners_part_local(self):
    from wotstat_spotting_points.geometry import buildLayoutBounds
    bounds = buildLayoutBounds(((-2, 1, -3), (2, 4, 3)),
                               ((-1, 0, -1), (1, 2, 1)))
    self.assertEqual(bounds.hull[0], (-2, 1, -3))
    self.assertEqual(bounds.hull[6], (2, 4, 3))
    self.assertEqual(bounds.turret[0], (-1, 0, -1))
    self.assertEqual(bounds.turret[6], (1, 2, 1))
```

- [ ] **Step 2: Run the test and confirm it fails because `buildLayoutBounds` is missing**

Run: `C:/Python27/python.exe -B -m unittest tests.test_geometry.GeometryTests.test_layout_bounds_keep_hull_and_turret_corners_part_local`

- [ ] **Step 3: Add the minimal geometry API**

```python
LayoutBounds = namedtuple('LayoutBounds', 'hull turret')

def buildLayoutBounds(hullBounds, turretBounds):
    return LayoutBounds(bboxPoints(*hullBounds), bboxPoints(*turretBounds))
```

Add `renderer.getLayoutBounds(vehicle)` which reads `TankPartIndexes.HULL` and
`TankPartIndexes.TURRET`, returns `None` for missing collision data, and otherwise
calls `buildLayoutBounds` without applying vehicle or turret offsets.

- [ ] **Step 4: Run the focused test and the geometry test module**

Run: `C:/Python27/python.exe -B -m unittest tests.test_geometry`

- [ ] **Step 5: Commit the geometry slice**

```powershell
git add -- tests/test_geometry.py res/scripts/client/gui/mods/wotstat_spotting_points/geometry.py res/scripts/client/gui/mods/wotstat_spotting_points/renderer.py
git commit -m "feat: expose part bounds for UI layout"
```

### Task 2: Invisible native layout anchors

**Files:**
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/controller.py`
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/marker_view.py`
- Modify: `tests/test_marker_view.py`
- Modify: `as3/src/wotstat/spottingpoints/MarkerOverlay.as`

**Interfaces:**
- Consumes: `getLayoutBounds(vehicle)` and `LayoutBounds.hull/turret`.
- Produces: AS3 anchor ids `hull0` through `hull7` and `turret0` through `turret7`.
- Produces: `MarkerOverlay.as_createLayoutAnchor(id:String):DisplayObject`.

- [ ] **Step 1: Write the failing marker-provider test**

Extend the marker-view fixture with `TankPartNames.HULL = 'hull'`,
`TankPartNames.TURRET = 'turret'`, and `FakeFlash.as_createLayoutAnchor`. Pass a
literal `LayoutBounds` to `updateMarkers` and assert that sixteen additional
native markers are created, hull providers use `vehicle.model.node('hull')`,
turret providers use `vehicle.model.node('turret')`, and a translated corner
provider resolves its part-local point through `MatrixProduct`.

- [ ] **Step 2: Run the focused test and confirm it fails on the missing layout-bound argument or API**

Run: `C:/Python27/python.exe -B -m unittest tests.test_marker_view.MarkerViewTests.test_layout_bounds_use_live_hull_and_turret_providers`

- [ ] **Step 3: Implement native anchor lifecycle**

Add a `_layoutMarkers` dictionary to `MarkerOverlayView`. Create each provider
as a product of a local translation matrix and the live part node:

```python
def _createPartMarkerProvider(point, partProvider):
    localMatrix = Matrix()
    localMatrix.setTranslate(point)
    provider = MatrixProduct()
    provider.a = localMatrix
    provider.b = partProvider
    return provider
```

`updateMarkers` accepts optional `layoutBounds`, creates missing anchors once,
and activates them with the visible markers. `clearMarkers`, scene activation,
and `_dispose` deactivate and clear both dictionaries. The controller supplies
`getLayoutBounds(vehicle)` on each throttled marker-data update.

In AS3, `as_createLayoutAnchor` creates an alpha-zero `Sprite`, stores it in a
`layoutAnchors` dictionary, and adds it to the display list. Clearing markers
also removes all anchor sprites.

- [ ] **Step 4: Run marker-view and controller tests**

Run: `C:/Python27/python.exe -B -m unittest tests.test_marker_view tests.test_controller`

- [ ] **Step 5: Commit the projection bridge**

```powershell
git add -- tests/test_marker_view.py res/scripts/client/gui/mods/wotstat_spotting_points/controller.py res/scripts/client/gui/mods/wotstat_spotting_points/marker_view.py as3/src/wotstat/spottingpoints/MarkerOverlay.as
git commit -m "feat: project hull and turret layout anchors"
```

### Task 3: Stable two-envelope callout layout

**Files:**
- Modify: `as3/src/wotstat/spottingpoints/MarkerOverlay.as`
- Modify: `as3/src/wotstat/spottingpoints/SpotPointMarker.as`
- Modify: `README.md`
- Modify: `docs/design.md`

**Interfaces:**
- Consumes: the sixteen projected layout anchors.
- Produces: `SpotPointMarker.layoutCallout(edgeX, edgeY, placement)` for
  `left`, `right`, and `top` placements.

- [ ] **Step 1: Replace the stateless greedy inputs with persistent state**

Store an object per point id with `side`, `stableY`, `pendingSide`,
`pendingFrames`, `displayX`, `displayY`, and `initialized`. Use these constants:

```actionscript
private static const BOUNDS_PADDING:Number = 18;
private static const SIDE_HYSTERESIS:Number = 36;
private static const SIDE_CONFIRM_FRAMES:int = 8;
private static const POSITION_DEADBAND:Number = 2;
private static const SMOOTH_TIME_MS:Number = 110;
```

Reset state on marker clearing, disposal, and application-size changes.

- [ ] **Step 2: Compute separate projected rectangles and stable regions**

Build padded hull/turret rectangles from `hull0..7` and `turret0..7`.
Use the existing visible-point envelope when either rectangle is invalid.
Reserve `top` above the union. Resolve each remaining marker against its group
rectangle and retain its previous side until it spends eight frames beyond the
36-pixel hysteresis band.

- [ ] **Step 3: Pack side slots and avoid both rectangles**

For each side, sort by the state's stable vertical key, clamp to screen
margins, run forward/backward spacing passes with `CALLOUT_GAP`, and move the
label edge past every hull or turret rectangle whose vertical range intersects
the label. Place the top label first so side slots also avoid its rectangle.

- [ ] **Step 4: Smooth displayed callouts and draw the new leaders**

Use `getTimer()` and frame elapsed time:

```actionscript
var alpha:Number = 1 - Math.exp(-elapsedMs / SMOOTH_TIME_MS);
if (Math.abs(targetX - state.displayX) > POSITION_DEADBAND) {
    state.displayX += (targetX - state.displayX) * alpha;
}
if (Math.abs(targetY - state.displayY) > POSITION_DEADBAND) {
    state.displayY += (targetY - state.displayY) * alpha;
}
```

For side leaders, end at the nearest label edge, set the diagonal run equal to
the absolute vertical delta when space permits, then draw the remaining segment
horizontally. The top leader ends at the nearest point on the lower label edge.

- [ ] **Step 5: Document the prototype behavior and compile both SWFs**

Run: `./build.ps1 -Version 0.3.0 -Python C:/Python27/python.exe`

- [ ] **Step 6: Run the complete Python suite and inspect package contents**

Run: `C:/Python27/python.exe -B -m unittest discover -s tests`

Inspect: `dist/wotstat.spotting-points_0.3.0.mtmod` contains the updated
`res/gui/flash/wotstatSpottingPointsMarkers.swf` and Python modules, with no
source SWCs or extracted game files.

- [ ] **Step 7: Commit the layout prototype**

```powershell
git add -- as3/src/wotstat/spottingpoints/MarkerOverlay.as as3/src/wotstat/spottingpoints/SpotPointMarker.as README.md docs/design.md
git commit -m "feat: stabilize UI point callouts"
```

### Task 4: «Мир танков» runtime validation

**Files:**
- No source files unless the smoke test exposes a concrete defect.

**Interfaces:**
- Consumes: `dist/wotstat.spotting-points_0.3.0.mtmod`.
- Produces: a visually inspected prototype in the running client.

- [ ] **Step 1: Install the MT package with the existing project/runtime workflow**

Do not touch unrelated mods and do not launch a second client instance.

- [ ] **Step 2: Validate in the hangar**

Enable UI points, reproduce the supplied camera angle, rotate the camera and
turret slowly through side-change thresholds, and verify the top slot, shorter
leaders, non-overlapping labels, hover, and absence of side/slot oscillation.

- [ ] **Step 3: Read the relevant fresh log tail**

Confirm there is no `WOTSTAT_SPOTTING_POINTS` exception from marker creation,
projection, layout, or disposal.

- [ ] **Step 4: Leave the client running**

Do not call any client shutdown, process termination, or window-close action.

