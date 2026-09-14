# Stable UI Callout Layout Prototype Design

## Goal

Build a «Мир танков»-only prototype of the hangar UI marker layout so labels
wrap the projected hull and turret separately, use shorter leaders, and remain
visually stable while the camera or turret rotates.

## Scope

- Target «Мир танков» (`mt-ru`) only.
- Keep the existing marker appearance, hover behavior, and point labels.
- Do not add a normal user-facing setting or persist layout state between
  overlay lifetimes. A transient developer-only layout debug flag may be
  exposed when the settings window is opened while Alt is held.
- Treat this as an interactive prototype: prioritize a useful in-client result
  over a new automated AS3 test platform.
- Do not close the game client after runtime validation.

## Projected avoidance bounds

The Python side derives eight hull corners and eight turret corners from the
collision bounding boxes already read by the renderer. Hull corners use the
vehicle matrix. Turret corners use the live turret joint matrix so the
projected turret rectangle follows turret rotation.

Each corner is attached to an invisible native hangar marker. AS3 reads their
screen positions every frame, builds separate convex hull and turret polygons,
and inflates each polygon by the callout clearance. Their AABBs are only cheap
outer envelopes for coarse side selection; collision and slot-edge calculations
use the polygons. A frame without all valid projected anchors is skipped instead
of replacing the forbidden geometry with an AABB approximation.

## Placement behavior

- Every label can use the shared slot above the combined vehicle envelope or a
  side slot. The top slot is not reserved for the `top` point.
- Side candidates for `rear`, `front`, `left`, `right`, and `top` avoid the hull
  polygon. Side candidates for `gunStatic` and `gunMoving` avoid the turret
  polygon. Every side candidate also avoids both projected polygons at its
  actual vertical span.
- The solver evaluates each point as the possible top-slot occupant and selects
  a complete plan that avoids overlaps whenever one fits. Top-leader length has
  extra weight so the point nearest that slot wins instead of accepting one very
  long top leader to make the remaining side leaders marginally shorter. A
  side-only plan is used only when no top placement fits. If no collision-free
  side placement exists, a high-penalty fallback minimizes the unavoidable
  overlap instead of hiding a label.
- Label rectangles share one collision pass, so labels from the two groups do
  not overlap.
- A side label first moves along its own avoidance polygon, then tries the
  next slot on that side. Moving to the opposite side is the last fallback.
- Labels are clamped to the screen margins, including long localized text.

Side leaders consist of a 45-degree diagonal leaving the marker and a short
horizontal segment entering the label. Whichever label occupies the top slot
connects to the nearest point on its lower edge.

## Temporal stability

AS3 recomputes a deterministic complete layout from the current projected
positions every frame. It first finishes collision resolution for all labels,
then applies every selected rectangle in one pass. There is no interpolation,
position deadband, hysteresis delay, or sequential slot animation. Dots and
labels therefore respond to the same rendered frame, and nothing continues
moving after the camera stops.

## Components and data flow

1. `geometry.py` creates plain hull and turret corner tuples that can be tested
   without game imports.
2. `renderer.py` obtains current collision bounds and exposes the layout corner
   data beside the existing spotting geometry.
3. `marker_view.py` creates and removes native marker providers for invisible
   layout anchors and visible point markers.
4. `MarkerOverlay.as` owns projected polygons, candidate plans, collision
   resolution, scoring, and atomic application of the selected plan.
5. `SpotPointMarker.as` accepts a polyline leader and explicit callout box
   position.

No shared game resource is replaced and no global input handler is changed.

## Layout debug

Holding Alt while opening the settings window reveals a non-persistent
`layoutDebug` checkbox. The overlay shows raw hull/turret corner projection,
the inflated convex forbidden polygons and the selected complete plan. Debug
drawing observes the same stateless solver inputs and results; it does not
maintain or animate a second layout model.

## Validation

- Add focused Python tests for bounding-box corner generation and layout anchor
  payloads.
- Run the existing Python test suite.
- Compile the marker and settings SWFs and build the mod package.
- Install and inspect the prototype in the «Мир танков» hangar at multiple
  camera angles, including the supplied long-callout angle and turret rotation.
- Check that labels do not oscillate between sides or adjacent slots.
- Leave the client running after the check.
