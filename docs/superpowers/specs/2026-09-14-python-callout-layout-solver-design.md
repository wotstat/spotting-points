# Python Callout Layout Solver Design

## Goal

Replace the expensive per-frame AS3 callout optimizer with a synchronous
Python 2.7 solver while preserving same-frame response. Improve close-zoom
fallbacks, leader readability, top-slot usage, and discrete temporal stability
without interpolation or delayed motion.

## Scope

- Preserve the existing marker appearance, labels, hover behavior, settings,
  native `GUI.HangarVehicleMarker` projection, and Alt-only layout debug mode.
- Keep building both `.mtmod` and `.wotmod` packages. Runtime acceptance for
  this iteration is the RU «Мир танков» 1.45 client.
- Do not replace shared game resources or add a global input handler.
- Do not add a user-facing tuning setting. All solver weights remain internal
  named constants.
- Add only focused tests for the production Python solver and its bridge.
  Visual behavior and frame cost are primarily validated in the RU client.

## Measured motivation

The current implementation recomputes projected polygons and evaluates up to
eight complete AS3 layout plans on every `ENTER_FRAME`. Each plan performs
repeated polygon spans, rectangle collisions, sorting, and allocation.

In the same static RU hangar scene, the hidden-callout baseline produced smooth
FPS samples around 58 to 59, while the complete current AS3 layout produced
about 23. A temporary benchmark performed one synchronous AS3 to Python to AS3
call per frame. AS3 created a nested geometry payload, Python read 62 numeric
fields, and Python returned seven placement dictionaries. Smooth FPS remained
around 57 to 58. The bridge cost is therefore small relative to the current AS3
optimizer. The benchmark code is throwaway and is not part of the product.

## Runtime architecture

`MarkerOverlay.as` remains responsible for display objects and screen-space
sampling. On each active frame it reads the visible marker positions and the
eight native hull and eight native turret anchors, then synchronously calls the
public Python callback `solveLayout(payload)`.

`MarkerOverlayView.solveLayout` converts the Scaleform `PyGFxValue` payload to
plain numbers and tuples, invokes one `CalloutLayoutSolver` owned by the view,
and returns a plain DAAPI-compatible result. The callback completes during the
same Scaleform frame. No deferred callback, animation, or second-frame apply is
introduced.

The production optimizer lives in a new game-independent
`layout_solver.py`. It imports no `BigWorld`, `GUI`, or `gui.*` module. It owns
geometry, candidate generation, scoring, bounded search, input caching, and the
last selected lane for each point.

The returned result contains one monotonically increasing `revision`, the raw
projected hull and turret outlines, their inflated forbidden polygons, and the
complete list of placements. Each placement contains the point id, lane,
callout rectangle, and the exact leader polyline used for both scoring and
drawing.

If the returned revision is unchanged, AS3 does not reposition callouts or
clear and redraw connector graphics. It may still update debug visibility.

## Bridge input

AS3 sends one object with this logical shape:

```text
{
  width: Number,
  height: Number,
  hull: [[x, y], ... eight corners],
  turret: [[x, y], ... eight corners],
  items: [{
    id: String,
    x: Number,
    y: Number,
    width: Number,
    height: Number,
    part: "hull" | "turret"
  }, ...]
}
```

Items are sorted by point id before crossing the bridge. A frame with missing
or non-finite projection data is skipped. The last valid layout remains visible
until valid data returns or marker state is cleared.

The solver quantizes screen size, marker positions, anchor positions, and label
sizes to quarter pixels for its cache signature. An unchanged signature returns
the existing revision without running candidate generation or search. Native
marker movement below the quarter-pixel threshold moves its child callout with
the point; the maximum stale screen-space correction is therefore subpixel and
does not create interpolation.

## Projected geometry

Python ports the existing monotonic-chain convex hull, convex inflation,
horizontal and vertical polygon spans, and rectangle/polygon intersection
operations from `LayoutGeometry.as`. Hull and turret remain separate inflated
convex polygons with `BOUNDS_PADDING = 18`.

Rectangle intrusion uses the exact intersection area between a callout
rectangle and a convex forbidden polygon. It is computed once per candidate by
clipping the polygon against the rectangle and applying the shoelace formula.
The optimizer never repeats this clipping while comparing complete plans.

After the Python implementation is active, the now-unused AS3 geometry solver
is removed. Debug rendering consumes the polygons returned by Python.

## Candidate model

Every visible label receives candidates in all three lanes: `left`, `right`,
and `top`. No point id owns or is excluded from a lane.

For each side, candidate vertical centers use the symmetric multipliers
`[0, -1, 1, -2, 2]` around the marker Y coordinate with
`CALLOUT_GAP = 28`. Upward and downward diagonal leaders are therefore offered
equally instead of accepting the first collision-free downward-shifted slot.
The near label edge is derived from the actual horizontal span of both projected
polygons at that candidate's vertical interval, with `EDGE_OFFSET = 18`.

Top candidates use horizontal multipliers `[0, -1, 1, -2, 2]` around the
marker X coordinate. Their step is `callout width + 12`. Their Y position is
above the topmost actual polygon span across that callout's horizontal
interval, again with `EDGE_OFFSET = 18`. Multiple labels may independently
select non-overlapping top candidates; there is no single shared top owner.

All coordinates are clamped to `SCREEN_MARGIN = 8`. Duplicate candidates
created by screen clamping are removed by lane and quarter-pixel rectangle.
Candidates intersecting a forbidden polygon are retained and scored, not
rejected. Thus every valid input has a complete plan even when the vehicle
projection fills nearly the whole screen.

## Leader geometry

Each candidate stores its finished screen-space polyline.

- A side leader starts at the marker, travels diagonally at exactly 45 degrees,
  and then travels horizontally into the near label edge. Before screen
  clamping, the label is moved far enough outward that its desired attachment
  Y can be reached by the 45-degree segment. After clamping, the attachment Y
  is restricted to the intersection of the label edge and
  `[markerY - horizontalReach, markerY + horizontalReach]`. A side candidate
  with no such intersection is omitted. Symmetric candidate generation permits
  the diagonal to go either up or down; top candidates keep the domain nonempty
  if screen bounds eliminate every side candidate.
- A top leader terminates at the center of the label's lower edge. It consumes
  the smaller screen-space delta with a diagonal segment at exactly 45 degrees,
  then completes the remaining delta with one horizontal or vertical segment.

`SpotPointMarker.as` receives and draws this returned polyline verbatim. It no
longer independently reconstructs an elbow, preventing scoring and rendering
from disagreeing.

## Cost model and fallback order

The optimizer minimizes a deterministic lexicographic score rather than relying
on arbitrarily large additive constants. The score tuple is:

```text
(
  screenOverflowCount,
  screenOverflowArea,
  leaderPointViolationCount,
  leaderPointPenetration,
  labelOverlapPairCount,
  labelOverlapArea,
  leaderCrossingCount,
  forbiddenPolygonCount,
  forbiddenOverlapArea,
  ordinaryCost
)
```

Lower tuple elements win at the first position that differs. Consequently no
number of cheaper compromises can accidentally outweigh one more severe
violation. Within one violation class, fewer affected objects or pairs wins
before the total area or penetration. `leaderPointPenetration` is the sum of
`POINT_CLEARANCE_RADIUS - segmentDistance`, with
`POINT_CLEARANCE_RADIUS = 10`.

Computed screen-overflow and label-overlap areas at or below `EPSILON` are
normalized to exact zero before tuple comparison. This prevents floating-point
rounding residue from outranking a real conflict later in the tuple.

The final `ordinaryCost` is total leader length, with top-leader length weighted
by `TOP_LEADER_WEIGHT = 1.15`, plus `LANE_SWITCH_PENALTY = 180` for each lane
change. Forbidden-polygon intrusion is therefore the cheapest exceptional
compromise and competes with leader length only after all more serious counts
and areas are equal.

When a candidate is added to a partial plan, pairwise scoring adds:

1. one leader crossing when the two polylines intersect, including contact at
   their endpoints;
2. one label-overlap pair and its exact intersection area when the two callout
   rectangles overlap;
3. one point violation and its penetration when either leader comes within ten
   pixels of the other marker point.

The point-distance check covers every segment, not only the diagonal. It is
bidirectional for each pair: the new leader is checked against existing points
and existing leaders are checked against the new point.

Screen overflow remains finite so malformed localization or an impossibly narrow
viewport still produces a complete deterministic plan. Reading from the
cheapest allowed compromise to the most severe, the strict fallback order is
therefore forbidden-polygon intrusion, leader crossing, label overlap,
leader-through-point, then screen overflow.

## Bounded deterministic search

The solver uses a deterministic constrained-greedy pass plus bounded repair
rather than an exhaustive product of candidates.

- Labels are processed by descending callout width, then point id. This stable
  order places the most constrained labels first.
- Candidate-local cost is precomputed once and candidates are sorted by that
  cost plus a stable lane/index signature.
- For the next label, candidates are compared against already selected labels.
  Evaluation stops at the first candidate without a pairwise conflict because
  no later candidate can improve its higher-priority score components.
- If the completed pass still contains a pairwise conflict, at most three repair
  passes reconsider only participating labels. Repair is capped at 192 pair
  scores.
- The resulting complete plan is applied atomically.

The domain has at most seven labels and at most fifteen raw candidates per
label. Fixed repair limits prevent input-dependent combinatorial growth.

## Temporal stability without jelly

The solver stores the last lane and discrete lane/offset candidate for each
point. A candidate in a lane different from the last selected lane pays
`LANE_SWITCH_PENALTY`. After a real switch, the new lane becomes the remembered
lane, so immediately switching back must beat the same penalty in the opposite
direction. This creates a score hysteresis band without a timer.

On changed input, the solver first rebuilds only those remembered candidates.
If a higher-priority conflict count increases, it builds the complete candidate
set only for the labels participating in that conflict and repairs them
atomically. Without a new conflict, a label is reconsidered only after its
switch-neutral weighted leader length has grown by more than 64 pixels since
its last evaluation. The stored baseline never includes the lane-switch
penalty.
A full all-label pass is reserved for initial layout, membership changes, and
the rare case where targeted repair cannot preserve the previous conflict
counts. There is no wall-clock callback: if motion stops, no later
reconsideration or move occurs.

There is no interpolation, easing, velocity, delayed slot queue, or retained
screen coordinate. Placement coordinates within the current lane follow every
changed input immediately, and all labels are applied together in one frame.
Camera rotation therefore cannot create trailing callouts after motion stops.

Lane, candidate, and last-evaluated-cost memory is deleted when a point
disappears and fully reset on vehicle change, marker clear, view disposal, or
invalidation of the overlay lifecycle.

## AS3 responsibilities after migration

`MarkerOverlay.as` performs only these hot-path operations:

1. gather valid screen positions and label dimensions;
2. invoke `solveLayout` synchronously;
3. ignore an unchanged revision;
4. atomically apply a changed complete plan;
5. pass returned geometry to the existing debug overlay.

`SpotPointMarker.as` converts the returned callout position and polyline from
overlay coordinates to its local coordinates, then redraws only for a changed
revision. Pulse animation, hit testing, label drawing, and visibility remain
unchanged.

The debug overlay continues to show orange/cyan raw projections, red inflated
convex forbidden polygons, and the yellow selected plan. Green candidates and
screen bounds do not return.

## Error handling

The Python bridge validates screen dimensions, the sixteen projected corners,
item ids, finite coordinates, and positive label dimensions before invoking the
solver. Invalid transient projection returns the previous revision without a
new plan.

An unexpected solver exception is logged once. The view marks its solver as
failed and subsequent frame callbacks return a small disabled result without
raising again, preventing per-frame traceback spam. A zero-delay BigWorld
callback disables UI points through the controller outside the synchronous
Scaleform call. Recreating the marker view constructs a new solver and clears
the failure state.

## Files and ownership

- Create `res/scripts/client/gui/mods/wotstat_spotting_points/layout_solver.py`
  for all pure geometry and optimization.
- Modify `marker_view.py` to own the solver, convert `PyGFxValue`, expose
  `solveLayout`, cache the failure state, and reset lifecycle state.
- Modify `MarkerOverlay.as` to gather bridge input and apply versioned results.
- Modify `SpotPointMarker.as` to draw returned polylines.
- Modify `LayoutDebugOverlay.as` to consume Python-returned projected and
  forbidden polygons.
- Remove `LayoutGeometry.as` after no production AS3 reference remains.
- Add focused solver tests and only the bridge/lifecycle tests needed for the
  new contract.
- Update README, design documentation, and the previous prototype spec to point
  to this superseding design.

## Validation

Automated tests cover these production behaviors:

1. multiple labels can occupy distinct top candidates;
2. a complete plan is returned when every label candidate intersects a
   forbidden polygon;
3. a non-crossing leader plan beats a crossing plan;
4. a leader avoids another marker's ten-pixel exclusion circle;
5. upward and downward side candidates are generated symmetrically;
6. lane hysteresis rejects a marginal reversal but accepts a materially better
   opposite lane;
7. identical quantized input returns an unchanged revision without a new
   search;
8. bridge conversion and lifecycle reset use real solver data without client
   mocks beyond the existing view seam.

Run the existing Python 2.7 suite, compile both SWFs, build both packages, and
verify package contents.

Install the `.mtmod` in the RU client and use WotStat REPL to inspect:

- ordinary three-quarter and side angles;
- top-down view with several viable top placements;
- extreme close zoom where labels must enter red polygons;
- camera rotation across a left/right preference boundary;
- leaders close to every foreign marker point;
- debug off and on;
- static and continuously changing layouts.

The reference performance targets are:

- an unchanged full-label layout within ten percent of the same scene's
  hidden-callout smooth FPS;
- cached callback work below 0.25 ms;
- changed-layout solver work below 4 ms at the 95th percentile during the
  controlled camera sweep;
- no new mod traceback or repeated error log.

RU acceptance on the installed 0.3.0 package used 189 changed frames in a
continuous camera sweep: median solve time was 1.158 ms, p95 was 2.690 ms, and
four frames required the all-label search. The following 240 cached callbacks
had a 0.198 ms median. Static smooth FPS was 58.3 both with callouts visible and
hidden. Ordinary, extreme-close, and top-down layouts, multiple top labels,
forbidden-zone fallback, and the Alt debug overlay were also inspected; the
current client log contained no solver error or traceback.

The Python view records separate rolling samples for the last 240 cached bridge
callbacks and changed-layout solves using `time.clock()`. It also records cache
hits, cache misses, and the current candidate count. A read-only diagnostic
method returns count, median, 95th percentile, and maximum on demand for WotStat
REPL inspection; it does not sort samples or write logs on the frame path.

The RU client remains running after validation.
