# Python Callout Layout Solver Implementation Plan

> **For agentic workers:** Implement sequentially in the current `main` checkout. Use focused TDD for Python behavior, compile AS3 after each bridge-facing change, and prefer RU-client REPL validation over additional synthetic UI tests.

**Goal:** Replace the per-frame AS3 callout optimizer with a synchronous, cached Python 2.7 solver that produces responsive complete layouts with strict conflict priorities and lane hysteresis.

**Architecture:** AS3 samples current projected anchors, marker positions, and label sizes, then calls Python once in the same frame. A game-independent Python solver builds convex obstacles, candidates, exact leader polylines, lexicographic costs, and a bounded constrained-greedy plan with conflict repair. AS3 applies a changed revision atomically and only draws the returned result.

**Tech Stack:** Python 2.7, Scaleform/ActionScript 3, DAAPI, Apache Royale 0.9.12, `unittest`, PowerShell, WotStat REPL, RU «Мир танков» 1.45.

**Spec:** `docs/superpowers/specs/2026-09-14-python-callout-layout-solver-design.md`

## Global Constraints

- Work directly in `main`; preserve unrelated user changes.
- Keep marker appearance, hover, settings, native projection, and Alt debug behavior.
- Do not add interpolation, delayed moves, slot queues, or per-frame Python logs.
- Keep tests focused; runtime layout quality and frame cost are accepted in the RU client.
- Leave the RU client running after validation.

### Task 1: Pure geometry, candidates, and deterministic solver

**Files:**
- Create: `res/scripts/client/gui/mods/wotstat_spotting_points/layout_solver.py`
- Create: `tests/test_layout_solver.py`

**Interfaces:**
- `CalloutLayoutSolver.solve(width, height, hull, turret, items)` returns a changed full result or an unchanged revision-only result.
- `CalloutLayoutSolver.reset()` clears cache, revision, and lane memory.
- Full results contain projected/raw/inflated polygons plus placements with exact leader polylines.

- [x] **Step 1: Add one focused failing geometry/candidate test**

Cover convex inflation/intersection area and assert that one item receives symmetric upward/downward side candidates plus five top candidates. Run:

```powershell
C:/Python27/python.exe -B tests/test_layout_solver.py LayoutSolverTests.test_geometry_and_candidates_are_symmetric
```

- [x] **Step 2: Implement the minimal pure geometry and candidate model**

Port monotonic-chain hull, octagonal convex inflation, horizontal/vertical spans, rectangle clipping/area, segment intersection, and point-to-segment distance. Generate `left`, `right`, and `top` candidates with quarter-pixel deduplication, screen clamping, exact 45-degree side elbows, octilinear top leaders ending at the lower-edge center, and returned polylines.

- [x] **Step 3: Add focused failing solver tests**

Use no more than four additional test methods to jointly cover:

- multiple labels selecting distinct top positions;
- red-zone fallback still returning a complete plan;
- lexicographic preference for non-crossing/non-overlapping/point-clear leaders;
- lane hysteresis, cache reuse, and lifecycle reset.

Run the module and confirm the new assertions fail before implementing search:

```powershell
C:/Python27/python.exe -B tests/test_layout_solver.py
```

- [x] **Step 4: Implement local scoring and bounded search**

Precompute candidate-local overflow, forbidden-overlap, leader length, bend, and lane-switch components. Select candidates in deterministic constrained order with early exit on a conflict-free candidate. If the complete pass still conflicts, run at most three repair passes for participating labels, capped at 192 pair scores. After repair, make one monotonic pass over bent routes using only already-built straighter candidates.

On a changed valid signature, update all remembered lanes and discrete candidate indices together and return the full result with a new revision. Rebuild the selected candidates on stable changed frames, then generate alternatives only for labels in a newly worsened conflict or whose leader cost grew by more than 64 pixels since its last evaluation. Reserve the all-label pass for initial layout, membership changes, and failed targeted repair. On an unchanged quarter-pixel signature, return only that revision. Remove lane/candidate/cost memory for absent ids.

- [x] **Step 5: Run the focused solver tests and commit the slice**

```powershell
C:/Python27/python.exe -B tests/test_layout_solver.py
git add -- tests/test_layout_solver.py res/scripts/client/gui/mods/wotstat_spotting_points/layout_solver.py
git commit -m "feat: add Python callout layout solver"
```

### Task 2: Synchronous DAAPI bridge and failure lifecycle

**Files:**
- Modify: `res/scripts/client/gui/mods/wotstat_spotting_points/marker_view.py`
- Modify: `tests/test_marker_view.py`

**Interfaces:**
- `MarkerOverlayView.solveLayout(payload)` is callable synchronously from AS3.
- `MarkerOverlayView.getLayoutPerformanceStats()` exposes bounded read-only timing data for REPL inspection.
- `clearMarkers()` and disposal reset solver state.

- [x] **Step 1: Add one failing bridge/lifecycle test**

Extend the existing `PyGFxValue`-like fixture so the same test checks attribute/index payload conversion, a full first result, a revision-only cache hit, performance counters, and reset from `clearMarkers()`.

```powershell
C:/Python27/python.exe -B tests/test_marker_view.py MarkerViewTests.test_layout_bridge_cache_stats_and_reset
```

- [x] **Step 2: Implement bridge conversion and timing**

Convert proxy objects to finite primitive data without treating them as dictionaries. Time total cached callbacks and changed solver calls with `time.clock()`, retain 240 samples in `deque`, and calculate median/p95/max only on diagnostic request.

Initialize the solver before `_populate`. Reset it during `clearMarkers()` and disposal. Return the previous revision for transient invalid projection.

- [x] **Step 3: Implement fail-once behavior**

Log an unexpected solver exception once, mark the view solver failed, return a small disabled response thereafter, and schedule `controller.setOption('showUiPoints', False)` through `BigWorld.callback(0.0, ...)` so teardown occurs outside the synchronous Scaleform callback.

- [x] **Step 4: Run marker-view and solver tests and commit**

```powershell
C:/Python27/python.exe -B -m unittest discover -s tests
git add -- tests/test_marker_view.py res/scripts/client/gui/mods/wotstat_spotting_points/marker_view.py
git commit -m "feat: bridge callout layout through DAAPI"
```

### Task 3: Thin AS3 sampling, atomic apply, and debug rendering

**Files:**
- Modify: `as3/src/wotstat/spottingpoints/MarkerOverlay.as`
- Modify: `as3/src/wotstat/spottingpoints/SpotPointMarker.as`
- Modify: `as3/src/wotstat/spottingpoints/LayoutDebugOverlay.as`
- Remove: `as3/src/wotstat/spottingpoints/LayoutGeometry.as`

**Interfaces:**
- `MarkerOverlay` declares public `solveLayout:Function` and sends the specified payload each active frame.
- `SpotPointMarker.layoutCallout(boxX, boxY, leader)` draws the exact returned polyline.
- `LayoutDebugOverlay.render(result)` consumes Python-returned geometry and selected placements.

- [x] **Step 1: Replace the AS3 optimizer with payload sampling**

Gather valid hull/turret anchor arrays and visible callout items, sorted by id. Include `part`, screen dimensions, marker coordinates, and current callout dimensions. Call Python synchronously once. Retain the last full result for Alt debug.

- [x] **Step 2: Apply only changed complete revisions**

Ignore revision-only responses. For a new full revision, resolve every placement by id and update all labels in the same call stack. Do not interpolate, ease, or sequence moves. Reset the local revision/result on clear and disposal.

- [x] **Step 3: Draw returned leaders and geometry verbatim**

Convert every returned overlay coordinate into marker-local coordinates and draw the returned polyline. Update debug drawing for raw boxes, red inflated polygons, and yellow selected rectangles/lines. Keep green candidates and screen borders absent.

- [x] **Step 4: Remove the obsolete AS3 geometry class and compile**

```powershell
./build.ps1 -Version 0.3.0 -Python C:/Python27/python.exe
```

- [x] **Step 5: Commit the AS3 migration**

```powershell
git add -- as3/src/wotstat/spottingpoints/MarkerOverlay.as as3/src/wotstat/spottingpoints/SpotPointMarker.as as3/src/wotstat/spottingpoints/LayoutDebugOverlay.as as3/src/wotstat/spottingpoints/LayoutGeometry.as
git commit -m "perf: move callout optimization to Python"
```

### Task 4: Documentation, full verification, and RU acceptance

**Files:**
- Modify: `README.md`
- Modify: `docs/design.md`
- Modify: `docs/superpowers/specs/2026-09-14-stable-ui-callout-layout-prototype-design.md`

- [x] **Step 1: Update documentation**

Describe the synchronous Python solver, strict fallback order, multiple top candidates, point clearance, discrete lane hysteresis, cache, and Alt debug data. Mark the previous prototype spec as superseded by the new design.

- [x] **Step 2: Run full automated verification and inspect packages**

```powershell
C:/Python27/python.exe -B -m unittest discover -s tests
./build.ps1 -Version 0.3.0 -Python C:/Python27/python.exe
C:/Python27/python.exe -B -m zipfile -l dist/wotstat.spotting-points_0.3.0.mtmod
C:/Python27/python.exe -B -m zipfile -l dist/wotstat.spotting-points_0.3.0.wotmod
git diff --check
```

- [x] **Step 3: Install only the rebuilt RU package**

Replace `E:\Games\Tanki\mods\1.45.0.0\wotstat.spotting-points_0.3.0.mtmod`. Reuse the existing client if safe; if a restart is required, close only that verified game process and launch one replacement instance.

- [x] **Step 4: Validate behavior through WotStat REPL**

Check ordinary, side, top-down, and extreme close zoom; rotate through left/right boundaries; toggle Alt debug; inspect leader-to-point clearance and simultaneous relocation. Query `getLayoutPerformanceStats()` after static and controlled moving-camera intervals.

Acceptance targets:

- unchanged seven-label scene is within 10% of hidden-callout smooth FPS;
- cached callback median is below 0.25 ms;
- changed solve p95 is below 4 ms;
- no repeated exception or new mod traceback.

- [x] **Step 5: Fix only concrete runtime defects, rerun proportional checks, and commit docs/final fixes**

```powershell
git add -- README.md docs/design.md docs/superpowers/specs/2026-09-14-stable-ui-callout-layout-prototype-design.md
git commit -m "docs: describe Python callout layout"
```

- [x] **Step 6: Final cleanliness check and leave the RU client running**

```powershell
git status --short
git log --oneline -5
```
