package wotstat.spottingpoints {
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.geom.Point;
    import flash.geom.Rectangle;
    import flash.utils.Dictionary;
    import net.wg.infrastructure.base.AbstractView;

    public class MarkerOverlay extends AbstractView {
        private static const CALLOUT_GAP:Number = 28;
        private static const EDGE_OFFSET:Number = 18;
        private static const SCREEN_MARGIN:Number = 8;
        private static const BOUNDS_PADDING:Number = 18;
        private static const TOP_LEADER_WEIGHT:Number = 4;
        private static const BLOCKED_PLACEMENT_PENALTY:Number = 1000000;
        private static const MAX_SLOT_ATTEMPTS:int = 16;
        private static const DEBUG_SLOT_ATTEMPTS:int = 5;

        private var markers:Dictionary = new Dictionary();
        private var layoutAnchors:Dictionary = new Dictionary();
        private var debugOverlay:LayoutDebugOverlay;
        private var layoutDebug:Boolean = false;
        private var active:Boolean = true;

        public function MarkerOverlay() {
            super();
        }

        override protected function onPopulate():void {
            super.onPopulate();
            mouseEnabled = false;
            mouseChildren = false;
            visible = true;
            debugOverlay = new LayoutDebugOverlay();
            debugOverlay.visible = false;
            addChildAt(debugOverlay, 0);
            addEventListener(Event.ENTER_FRAME, onEnterFrame);
        }

        override protected function allowHandleInput():Boolean {
            return false;
        }

        public function as_createMarker(id:String,
                                        label:String):DisplayObject {
            var existing:SpotPointMarker = markers[id] as SpotPointMarker;
            if (existing != null) {
                return existing;
            }
            var marker:SpotPointMarker = new SpotPointMarker(id, label);
            markers[id] = marker;
            addChild(marker);
            return marker;
        }

        public function as_createLayoutAnchor(id:String):DisplayObject {
            var existing:DisplayObject = layoutAnchors[id] as DisplayObject;
            if (existing != null) {
                return existing;
            }
            var anchor:Sprite = new Sprite();
            anchor.alpha = 0;
            anchor.mouseEnabled = false;
            anchor.mouseChildren = false;
            layoutAnchors[id] = anchor;
            addChild(anchor);
            return anchor;
        }

        public function as_updateMarkers(data:Array,
                                         hoveredId:String):void {
            for each (var item:Object in data) {
                var id:String = String(item.id);
                var marker:SpotPointMarker = markers[id] as SpotPointMarker;
                if (marker != null) {
                    marker.setData(
                        String(item.label), Boolean(item.showLabel));
                    marker.setHovered(id == hoveredId);
                }
            }
        }

        public function as_hitTest(cursorX:Number, cursorY:Number):String {
            if (!active) {
                return null;
            }
            var stageX:Number = (cursorX + 1) * App.appWidth * 0.5;
            var stageY:Number = (1 - cursorY) * App.appHeight * 0.5;
            for each (var marker:SpotPointMarker in markers) {
                if (marker.visible && marker.hitTestUi(stageX, stageY)) {
                    return marker.pointId;
                }
            }
            return null;
        }

        public function as_setActive(value:Boolean):void {
            if (active == value) {
                return;
            }
            active = value;
            visible = value;
        }

        public function as_setLayoutDebug(value:Boolean):void {
            layoutDebug = value;
            if (debugOverlay != null) {
                debugOverlay.visible = value;
                if (!value) {
                    debugOverlay.clear();
                }
            }
        }

        public function as_clearMarkers():void {
            for (var key:Object in markers) {
                removeMarker(String(key));
            }
            for (key in layoutAnchors) {
                removeChild(layoutAnchors[key] as DisplayObject);
                delete layoutAnchors[key];
            }
            if (debugOverlay != null) {
                debugOverlay.clear();
            }
        }

        public function as_removeMarker(id:String):void {
            removeMarker(id);
        }

        private function onEnterFrame(event:Event):void {
            if (active) {
                layoutCallouts();
            }
        }

        private function layoutCallouts():void {
            var visibleMarkers:Array = [];
            var width:Number = App.appWidth;
            var height:Number = App.appHeight;
            if (width <= 0 || height <= 0) {
                return;
            }
            var marker:SpotPointMarker;
            for each (marker in markers) {
                if (!marker.visible) {
                    continue;
                }
                visibleMarkers.push(marker);
            }
            if (visibleMarkers.length == 0) {
                if (debugOverlay != null) {
                    debugOverlay.clear();
                }
                return;
            }

            var hullPart:Object = projectedPart("hull");
            var turretPart:Object = projectedPart("turret");
            if (hullPart == null || turretPart == null) {
                if (debugOverlay != null) {
                    debugOverlay.clear();
                }
                return;
            }
            var items:Array = [];

            for each (marker in visibleMarkers) {
                if (!marker.isCalloutVisible) {
                    continue;
                }
                var position:Point = displayPosition(marker);
                var avoidancePart:Object =
                    isTurretPoint(marker.pointId) ? turretPart : hullPart;
                items.push({
                    "marker": marker,
                    "markerX": position.x,
                    "markerY": position.y,
                    "avoidance": avoidancePart.obstacle,
                    "avoidanceBounds": avoidancePart.bounds
                });
            }

            var obstacles:Array = [
                hullPart.obstacle as Array,
                turretPart.obstacle as Array
            ];
            items.sort(comparePointId);
            var plan:Object = chooseLayoutPlan(
                items, obstacles, width, height, layoutDebug);
            if (plan != null) {
                applyLayoutPlan(plan);
            }
            if (debugOverlay != null && layoutDebug) {
                debugOverlay.render(
                    hullPart, turretPart,
                    plan != null ? plan.candidates as Array : null,
                    plan != null ? plan.placements as Array : null,
                    width, height);
            }
        }

        private function displayPosition(value:DisplayObject):Point {
            return globalToLocal(value.localToGlobal(new Point(0, 0)));
        }

        private function projectedPart(prefix:String):Object {
            var points:Array = [];
            for (var index:int = 0; index < 8; index++) {
                var anchor:DisplayObject = layoutAnchors[
                    prefix + index] as DisplayObject;
                if (anchor == null) {
                    return null;
                }
                var point:Point = displayPosition(anchor);
                if (!validPoint(point)) {
                    return null;
                }
                points.push(point);
            }
            var outline:Array = LayoutGeometry.convexHull(points);
            if (outline.length < 3) {
                return null;
            }
            var obstacle:Array = LayoutGeometry.inflateConvexPolygon(
                outline, BOUNDS_PADDING);
            var bounds:Rectangle = LayoutGeometry.polygonBounds(obstacle);
            if (bounds == null || bounds.width < 1 || bounds.height < 1) {
                return null;
            }
            return {
                "points": points,
                "outline": outline,
                "obstacle": obstacle,
                "bounds": bounds
            };
        }

        private function validPoint(point:Point):Boolean {
            return point != null && !isNaN(point.x) && !isNaN(point.y) &&
                   isFinite(point.x) && isFinite(point.y);
        }

        private function isTurretPoint(pointId:String):Boolean {
            return pointId == "gunStatic" || pointId == "gunMoving";
        }

        private function compareProjectedOrder(a:Object, b:Object):Number {
            var difference:Number = Number(a.markerY) - Number(b.markerY);
            if (difference != 0) {
                return difference;
            }
            var aId:String = SpotPointMarker(a.marker).pointId;
            var bId:String = SpotPointMarker(b.marker).pointId;
            return aId < bId ? -1 : (aId == bId ? 0 : 1);
        }

        private function comparePointId(a:Object, b:Object):Number {
            var aId:String = SpotPointMarker(a.marker).pointId;
            var bId:String = SpotPointMarker(b.marker).pointId;
            return aId < bId ? -1 : (aId == bId ? 0 : 1);
        }

        private function chooseLayoutPlan(
                items:Array, obstacles:Array, width:Number,
                height:Number, collectDebug:Boolean):Object {
            var best:Object = null;
            for each (var item:Object in items) {
                var debugCandidates:Array = collectDebug ? [] : null;
                var candidate:Object = buildLayoutPlan(
                    items, item, obstacles, width, height,
                    debugCandidates);
                if (candidate != null && (best == null ||
                        Number(candidate.score) < Number(best.score) ||
                        (Number(candidate.score) == Number(best.score) &&
                         String(candidate.signature) <
                         String(best.signature)))) {
                    best = candidate;
                }
            }
            if (best == null) {
                debugCandidates = collectDebug ? [] : null;
                best = buildLayoutPlan(
                    items, null, obstacles, width, height,
                    debugCandidates);
            }
            return best;
        }

        private function buildLayoutPlan(
                items:Array, topItem:Object, obstacles:Array, width:Number,
                height:Number, debugCandidates:Array):Object {
            var plan:Object = {
                "placements": [],
                "score": 0,
                "signature": "",
                "candidates": debugCandidates
            };
            var occupied:Array = [];
            if (topItem != null) {
                var top:Object = topPlacement(
                    topItem, obstacles, width, height,
                    debugCandidates);
                if (top == null) {
                    return null;
                }
                appendPlannedPlacement(
                    plan, topItem, top, occupied,
                    obstacles, false);
            }

            var left:Array = [];
            var right:Array = [];
            for each (var item:Object in items) {
                if (item === topItem) {
                    continue;
                }
                var side:String = preferredSide(item, width);
                (side == "left" ? left : right).push(item);
            }
            planSide(left, "left", obstacles, occupied,
                     plan, width, height, debugCandidates);
            planSide(right, "right", obstacles, occupied,
                     plan, width, height, debugCandidates);
            return plan;
        }

        private function preferredSide(item:Object, width:Number):String {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var bounds:Rectangle = item.avoidanceBounds as Rectangle;
            var leftUsable:Boolean = sideUsable(
                "left", bounds, marker.calloutWidth, width);
            var rightUsable:Boolean = sideUsable(
                "right", bounds, marker.calloutWidth, width);
            if (leftUsable && !rightUsable) {
                return "left";
            }
            if (rightUsable && !leftUsable) {
                return "right";
            }
            var leftDistance:Number = Math.abs(
                Number(item.markerX) - (bounds.left - EDGE_OFFSET));
            var rightDistance:Number = Math.abs(
                Number(item.markerX) - (bounds.right + EDGE_OFFSET));
            if (leftDistance != rightDistance) {
                return leftDistance < rightDistance ? "left" : "right";
            }
            return prefersLeft(marker.pointId) ? "left" : "right";
        }

        private function prefersLeft(pointId:String):Boolean {
            return pointId == "rear" || pointId == "left" ||
                   pointId == "gunStatic";
        }

        private function sideUsable(side:String, bounds:Rectangle,
                                    calloutWidth:Number,
                                    screenWidth:Number):Boolean {
            if (side == "left") {
                return bounds.left - EDGE_OFFSET - SCREEN_MARGIN >=
                       calloutWidth;
            }
            return screenWidth - SCREEN_MARGIN -
                   (bounds.right + EDGE_OFFSET) >= calloutWidth;
        }

        private function topPlacement(item:Object, obstacles:Array,
                                      width:Number,
                                      height:Number,
                                      debugCandidates:Array):Object {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var boxX:Number = clamp(
                Number(item.markerX) - marker.calloutWidth * 0.5,
                SCREEN_MARGIN,
                Math.max(SCREEN_MARGIN,
                         width - SCREEN_MARGIN - marker.calloutWidth));
            var topEdge:Number = Number.POSITIVE_INFINITY;
            for each (var obstacle:Array in obstacles) {
                var span:Object = LayoutGeometry.verticalSpan(
                    obstacle, boxX, boxX + marker.calloutWidth);
                if (span != null) {
                    topEdge = Math.min(topEdge, Number(span.min));
                }
            }
            if (!isFinite(topEdge)) {
                topEdge = Number(item.markerY);
            }
            var boxY:Number = clamp(
                topEdge - EDGE_OFFSET - marker.calloutHeight,
                SCREEN_MARGIN,
                Math.max(SCREEN_MARGIN,
                         height - SCREEN_MARGIN - marker.calloutHeight));
            var rect:Rectangle = new Rectangle(
                boxX, boxY, marker.calloutWidth, marker.calloutHeight);
            var valid:Boolean = !intersectsObstacles(rect, obstacles);
            recordDebugCandidate(
                debugCandidates, item, rect, "top", valid);
            if (!valid) {
                return null;
            }
            return {
                "x": boxX,
                "y": boxY,
                "placement": "top",
                "rect": rect
            };
        }

        private function planSide(items:Array, side:String,
                                  obstacles:Array, occupied:Array,
                                  plan:Object, width:Number,
                                  height:Number,
                                  debugCandidates:Array):void {
            if (items.length == 0) {
                return;
            }
            items.sort(compareProjectedOrder);
            var minimum:Number = SCREEN_MARGIN +
                SpotPointMarker(items[0].marker).calloutHeight * 0.5;
            var maximum:Number = height - minimum;
            var previous:Number = minimum - CALLOUT_GAP;
            var item:Object;
            for each (item in items) {
                item.slotY = Math.max(
                    clamp(Number(item.markerY), minimum, maximum),
                    previous + CALLOUT_GAP);
                previous = Number(item.slotY);
            }
            if (Number(items[items.length - 1].slotY) > maximum) {
                items[items.length - 1].slotY = maximum;
                for (var index:int = items.length - 2; index >= 0; index--) {
                    items[index].slotY = Math.min(
                        Number(items[index].slotY),
                        Number(items[index + 1].slotY) - CALLOUT_GAP);
                }
            }
            if (Number(items[0].slotY) < minimum) {
                items[0].slotY = minimum;
                for (index = 1; index < items.length; index++) {
                    items[index].slotY = Math.max(
                        Number(items[index].slotY),
                        Number(items[index - 1].slotY) + CALLOUT_GAP);
                }
            }
            for each (item in items) {
                var chosenSide:String = side;
                var blocked:Boolean = false;
                var placement:Object = findSidePlacement(
                    item, chosenSide, Number(item.slotY), obstacles,
                    occupied, width, height, debugCandidates);
                if (placement == null) {
                    chosenSide = side == "left" ? "right" : "left";
                    placement = findSidePlacement(
                        item, chosenSide, Number(item.slotY),
                        obstacles, occupied, width, height,
                        debugCandidates);
                }
                if (placement == null) {
                    chosenSide = side;
                    placement = sidePlacement(
                        item, chosenSide, Number(item.slotY),
                        obstacles, width, height);
                    blocked = Boolean(placement.blocked) ||
                        overlapsLabels(
                            placement.rect as Rectangle, occupied);
                    recordDebugCandidate(
                        debugCandidates, item,
                        placement.rect as Rectangle,
                        chosenSide, !blocked);
                }
                appendPlannedPlacement(
                    plan, item, placement, occupied,
                    obstacles, blocked);
            }
        }

        private function appendPlannedPlacement(
                plan:Object, item:Object, placement:Object,
                occupied:Array, obstacles:Array,
                blocked:Boolean):void {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var rect:Rectangle = placement.rect as Rectangle;
            plan.placements.push({
                "item": item,
                "placement": placement
            });
            var cost:Number = placementCost(item, placement);
            if (String(placement.placement) == "top") {
                cost *= TOP_LEADER_WEIGHT;
            }
            plan.score += cost;
            if (blocked || Boolean(placement.blocked) ||
                    isBlocked(rect, occupied, obstacles)) {
                plan.score += BLOCKED_PLACEMENT_PENALTY;
            }
            plan.signature += "|" + marker.pointId + ":" +
                              String(placement.placement);
            occupied.push(rect);
        }

        private function placementCost(item:Object,
                                       placement:Object):Number {
            var rect:Rectangle = placement.rect as Rectangle;
            var targetX:Number;
            var targetY:Number;
            if (String(placement.placement) == "left") {
                targetX = rect.right;
                targetY = rect.y + rect.height * 0.5;
            } else if (String(placement.placement) == "right") {
                targetX = rect.left;
                targetY = rect.y + rect.height * 0.5;
            } else {
                targetX = clamp(Number(item.markerX), rect.left, rect.right);
                targetY = rect.bottom;
            }
            var deltaX:Number = targetX - Number(item.markerX);
            var deltaY:Number = targetY - Number(item.markerY);
            return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        }

        private function applyLayoutPlan(plan:Object):void {
            for each (var entry:Object in plan.placements) {
                var marker:SpotPointMarker = entry.item.marker as
                    SpotPointMarker;
                var placement:Object = entry.placement;
                marker.layoutCallout(
                    Number(placement.x), Number(placement.y),
                    String(placement.placement));
            }
        }

        private function findSidePlacement(
                item:Object, side:String, desiredY:Number,
                obstacles:Array, occupied:Array,
                width:Number, height:Number,
                debugCandidates:Array):Object {
            var selected:Object = null;
            for (var attempt:int = 0; attempt < MAX_SLOT_ATTEMPTS;
                    attempt++) {
                var distance:Number = Math.ceil(attempt * 0.5) * CALLOUT_GAP;
                var direction:Number = attempt == 0 ? 0 :
                    (attempt % 2 == 1 ? -1 : 1);
                var centerY:Number = desiredY + distance * direction;
                var placement:Object = sidePlacement(
                    item, side, centerY, obstacles, width, height);
                var valid:Boolean = !Boolean(placement.blocked) &&
                    !overlapsLabels(
                        placement.rect as Rectangle, occupied);
                recordDebugCandidate(
                    debugCandidates, item,
                    placement.rect as Rectangle,
                    side, valid);
                if (valid && selected == null) {
                    selected = placement;
                    if (debugCandidates == null) {
                        return selected;
                    }
                }
                if (selected != null && debugCandidates != null &&
                        attempt + 1 >= DEBUG_SLOT_ATTEMPTS) {
                    return selected;
                }
            }
            return selected;
        }

        private function sidePlacement(
                item:Object, side:String, centerY:Number,
                obstacles:Array, width:Number, height:Number):Object {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var halfHeight:Number = marker.calloutHeight * 0.5;
            centerY = clamp(
                centerY, SCREEN_MARGIN + halfHeight,
                height - SCREEN_MARGIN - halfHeight);
            var boxY:Number = centerY - halfHeight;
            var groupSpan:Object = LayoutGeometry.horizontalSpan(
                item.avoidance as Array, boxY,
                boxY + marker.calloutHeight);
            var edgeX:Number = side == "left" ?
                (groupSpan != null ? Number(groupSpan.min) :
                 Number(item.markerX)) - EDGE_OFFSET :
                (groupSpan != null ? Number(groupSpan.max) :
                 Number(item.markerX)) + EDGE_OFFSET;
            for each (var obstacle:Array in obstacles) {
                var span:Object = LayoutGeometry.horizontalSpan(
                    obstacle, boxY, boxY + marker.calloutHeight);
                if (span != null) {
                    edgeX = side == "left" ?
                        Math.min(edgeX, Number(span.min) - EDGE_OFFSET) :
                        Math.max(edgeX, Number(span.max) + EDGE_OFFSET);
                }
            }
            var boxX:Number = side == "left" ?
                edgeX - marker.calloutWidth : edgeX;
            boxX = clamp(
                boxX, SCREEN_MARGIN,
                Math.max(SCREEN_MARGIN,
                         width - SCREEN_MARGIN - marker.calloutWidth));
            var rect:Rectangle = new Rectangle(
                boxX, boxY, marker.calloutWidth, marker.calloutHeight);
            return {
                "x": boxX,
                "y": boxY,
                "placement": side,
                "rect": rect,
                "blocked": intersectsObstacles(rect, obstacles)
            };
        }

        private function isBlocked(rect:Rectangle, occupied:Array,
                                   obstacles:Array):Boolean {
            return intersectsObstacles(rect, obstacles) ||
                   overlapsLabels(rect, occupied);
        }

        private function intersectsObstacles(rect:Rectangle,
                                             obstacles:Array):Boolean {
            for each (var obstacle:Array in obstacles) {
                if (LayoutGeometry.rectangleIntersectsPolygon(
                        rect, obstacle)) {
                    return true;
                }
            }
            return false;
        }

        private function recordDebugCandidate(
                values:Array, item:Object, rect:Rectangle, placement:String,
                valid:Boolean):void {
            if (values == null || rect == null) {
                return;
            }
            values.push({
                "pointId": SpotPointMarker(item.marker).pointId,
                "rect": rect.clone(),
                "placement": placement,
                "valid": valid
            });
        }

        private function overlapsLabels(rect:Rectangle,
                                        occupied:Array):Boolean {
            var probe:Rectangle = rect.clone();
            probe.inflate(2, 2);
            for each (var other:Rectangle in occupied) {
                if (probe.intersects(other)) {
                    return true;
                }
            }
            return false;
        }

        private function clamp(value:Number, minimum:Number,
                               maximum:Number):Number {
            return Math.max(minimum, Math.min(maximum, value));
        }

        private function removeMarker(id:String):void {
            var marker:SpotPointMarker = markers[id] as SpotPointMarker;
            if (marker == null) {
                return;
            }
            removeChild(marker);
            marker.dispose();
            delete markers[id];
        }

        override protected function onBeforeDispose():void {
            removeEventListener(Event.ENTER_FRAME, onEnterFrame);
            as_clearMarkers();
            super.onBeforeDispose();
        }

        override protected function onDispose():void {
            markers = null;
            layoutAnchors = null;
            debugOverlay = null;
            super.onDispose();
        }
    }
}
