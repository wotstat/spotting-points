# Stable UI Callout Layout Prototype Design

## Goal

Build a «Мир танков»-only prototype of the hangar UI marker layout so labels
wrap the projected hull and turret separately, use shorter leaders, and remain
visually stable while the camera or turret rotates.

## Scope

- Target «Мир танков» (`mt-ru`) only.
- Keep the existing marker appearance, hover behavior, and point labels.
- Do not add settings or persist layout state between overlay lifetimes.
- Treat this as an interactive prototype: prioritize a useful in-client result
  over a new automated AS3 test platform.
- Do not close the game client after runtime validation.

## Projected avoidance bounds

The Python side derives eight hull corners and eight turret corners from the
collision bounding boxes already read by the renderer. Hull corners use the
vehicle matrix. Turret corners use the live turret joint matrix so the
projected turret rectangle follows turret rotation.

Each corner is attached to an invisible native hangar marker. AS3 reads their
screen positions every frame and computes padded axis-aligned screen rectangles
for the hull and turret. Missing or invalid bounds fall back to the existing
point envelope for that frame instead of hiding the visible markers.

## Placement behavior

- `rear`, `front`, `left`, and `right` use slots around the hull rectangle.
- `gunStatic` and `gunMoving` use slots around the turret rectangle.
- `top` owns a dedicated slot above the upper edge of the combined vehicle
  envelope.
- Label rectangles share one collision pass, so labels from the two groups do
  not overlap.
- A side label first moves along its own avoidance rectangle, then tries the
  next slot on that side. Moving to the opposite side is the last fallback.
- Labels are clamped to the screen margins, including long localized text.

Side leaders consist of a 45-degree diagonal leaving the marker and a short
horizontal segment entering the label. The top label connects to the nearest
point on its lower edge. The leader is drawn to the label's displayed position,
not an unsmoothed target.

## Temporal stability

AS3 stores a layout state per point id: region, side, order, displayed
position, and pending reassignment state.

- A side changes only after the marker remains beyond a screen-space
  hysteresis band for several consecutive frames, or the current side becomes
  invalid.
- Vertical order changes only when an overlap or inversion persists for
  several frames.
- Displayed label positions approach target positions using elapsed-time-based
  smoothing, so behavior does not depend on frame rate.
- Target movements of two pixels or less are ignored.
- Dots continue to follow their native marker providers without smoothing.
- All stability state resets when markers are cleared, the selected vehicle
  changes, the overlay is disposed, or the application dimensions change.

## Components and data flow

1. `geometry.py` creates plain hull and turret corner tuples that can be tested
   without game imports.
2. `renderer.py` obtains current collision bounds and exposes the layout corner
   data beside the existing spotting geometry.
3. `marker_view.py` creates and removes native marker providers for invisible
   layout anchors and visible point markers.
4. `MarkerOverlay.as` owns projected rectangles, candidate slots, persistent
   layout state, collision resolution, hysteresis, and smoothing.
5. `SpotPointMarker.as` accepts a polyline leader and explicit callout box
   position.

No shared game resource is replaced and no global input handler is changed.

## Validation

- Add focused Python tests for bounding-box corner generation and layout anchor
  payloads.
- Run the existing Python test suite.
- Compile the marker and settings SWFs and build the mod package.
- Install and inspect the prototype in the «Мир танков» hangar at multiple
  camera angles, including the supplied long-callout angle and turret rotation.
- Check that labels do not oscillate between sides or adjacent slots.
- Leave the client running after the check.

