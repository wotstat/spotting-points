package wotstat.spottingpoints {
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.geom.Point;
    import flash.geom.Rectangle;
    import flash.utils.getTimer;
    import flash.utils.Dictionary;
    import net.wg.infrastructure.base.AbstractView;

    public class MarkerOverlay extends AbstractView {
        private static const CALLOUT_GAP:Number = 28;
        private static const EDGE_OFFSET:Number = 18;
        private static const SCREEN_MARGIN:Number = 8;
        private static const BOUNDS_PADDING:Number = 18;
        private static const SIDE_HYSTERESIS:Number = 36;
        private static const SIDE_CONFIRM_FRAMES:int = 8;
        private static const POSITION_DEADBAND:Number = 2;
        private static const SMOOTH_TIME_MS:Number = 110;
        private static const MAX_SLOT_ATTEMPTS:int = 16;

        private var markers:Dictionary = new Dictionary();
        private var layoutAnchors:Dictionary = new Dictionary();
        private var layoutStates:Dictionary = new Dictionary();
        private var active:Boolean = true;
        private var lastLayoutTime:int = 0;
        private var lastAppWidth:Number = -1;
        private var lastAppHeight:Number = -1;

        public function MarkerOverlay() {
            super();
        }

        override protected function onPopulate():void {
            super.onPopulate();
            mouseEnabled = false;
            mouseChildren = false;
            visible = true;
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
            layoutCallouts();
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

        public function as_clearMarkers():void {
            for (var key:Object in markers) {
                removeMarker(String(key));
            }
            for (key in layoutAnchors) {
                removeChild(layoutAnchors[key] as DisplayObject);
                delete layoutAnchors[key];
            }
            resetLayoutState();
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
            if (width != lastAppWidth || height != lastAppHeight) {
                resetLayoutState();
                lastAppWidth = width;
                lastAppHeight = height;
            }
            var now:int = getTimer();
            var elapsedMs:Number = lastLayoutTime > 0 ?
                Math.max(0, now - lastLayoutTime) : 16;
            lastLayoutTime = now;
            var smoothingAlpha:Number = 1 - Math.exp(
                -elapsedMs / SMOOTH_TIME_MS);
            var left:Array = [];
            var right:Array = [];
            var topItem:Object = null;
            var marker:SpotPointMarker;
            for each (marker in markers) {
                if (!marker.visible) {
                    continue;
                }
                visibleMarkers.push(marker);
            }
            if (visibleMarkers.length == 0) {
                return;
            }

            var fallbackBounds:Rectangle = visiblePointBounds(visibleMarkers);
            var hullBounds:Rectangle = projectedBounds("hull");
            var turretBounds:Rectangle = projectedBounds("turret");
            if (hullBounds == null || turretBounds == null) {
                hullBounds = fallbackBounds;
                turretBounds = fallbackBounds;
            }
            if (hullBounds == null || turretBounds == null) {
                return;
            }
            var vehicleBounds:Rectangle = hullBounds.union(turretBounds);

            for each (marker in visibleMarkers) {
                if (!marker.isCalloutVisible) {
                    continue;
                }
                var position:Point = displayPosition(marker);
                var region:String = isTurretPoint(marker.pointId) ?
                    "turret" : "hull";
                var avoidance:Rectangle = region == "turret" ?
                    turretBounds : hullBounds;
                var state:Object = layoutState(
                    marker.pointId, region, position.y);
                updateStableOrder(state, position.y);
                var item:Object = {
                    "marker": marker,
                    "markerX": position.x,
                    "markerY": position.y,
                    "avoidance": avoidance,
                    "state": state
                };
                if (marker.pointId == "top") {
                    state.side = "top";
                    topItem = item;
                    continue;
                }
                var side:String = updateStableSide(
                    item, width);
                (side == "left" ? left : right).push(item);
            }

            var occupied:Array = [];
            var avoidanceBounds:Array = [hullBounds, turretBounds];
            if (topItem != null) {
                occupied.push(layoutTop(
                    topItem, vehicleBounds, width, height,
                    smoothingAlpha));
            }
            layoutSide(left, "left", avoidanceBounds, occupied,
                       width, height, smoothingAlpha);
            layoutSide(right, "right", avoidanceBounds, occupied,
                       width, height, smoothingAlpha);
        }

        private function displayPosition(value:DisplayObject):Point {
            return globalToLocal(value.localToGlobal(new Point(0, 0)));
        }

        private function projectedBounds(prefix:String):Rectangle {
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
            return boundsForPoints(points, true);
        }

        private function visiblePointBounds(values:Array):Rectangle {
            var points:Array = [];
            for each (var marker:SpotPointMarker in values) {
                var point:Point = displayPosition(marker);
                if (validPoint(point)) {
                    points.push(point);
                }
            }
            return boundsForPoints(points, false);
        }

        private function boundsForPoints(points:Array,
                                         rejectCollapsed:Boolean):Rectangle {
            if (points.length == 0) {
                return null;
            }
            var minX:Number = Number(points[0].x);
            var maxX:Number = minX;
            var minY:Number = Number(points[0].y);
            var maxY:Number = minY;
            for each (var point:Point in points) {
                minX = Math.min(minX, point.x);
                maxX = Math.max(maxX, point.x);
                minY = Math.min(minY, point.y);
                maxY = Math.max(maxY, point.y);
            }
            if (rejectCollapsed && (maxX - minX < 1 || maxY - minY < 1)) {
                return null;
            }
            return new Rectangle(
                minX - BOUNDS_PADDING, minY - BOUNDS_PADDING,
                maxX - minX + BOUNDS_PADDING * 2,
                maxY - minY + BOUNDS_PADDING * 2);
        }

        private function validPoint(point:Point):Boolean {
            return point != null && !isNaN(point.x) && !isNaN(point.y) &&
                   isFinite(point.x) && isFinite(point.y);
        }

        private function isTurretPoint(pointId:String):Boolean {
            return pointId == "gunStatic" || pointId == "gunMoving";
        }

        private function layoutState(pointId:String, region:String,
                                     markerY:Number):Object {
            var state:Object = layoutStates[pointId];
            if (state == null) {
                state = {
                    "region": region,
                    "side": null,
                    "order": markerY,
                    "stableY": markerY,
                    "pendingSide": null,
                    "pendingFrames": 0,
                    "pendingOrder": 0,
                    "pendingOrderFrames": 0,
                    "displayX": 0,
                    "displayY": 0,
                    "initialized": false
                };
                layoutStates[pointId] = state;
            } else {
                state.region = region;
            }
            return state;
        }

        private function updateStableOrder(state:Object,
                                           markerY:Number):void {
            var delta:Number = markerY - Number(state.stableY);
            if (Math.abs(delta) <= CALLOUT_GAP * 0.5) {
                state.pendingOrderFrames = 0;
                return;
            }
            var direction:Number = delta < 0 ? -1 : 1;
            if (Number(state.pendingOrder) != direction) {
                state.pendingOrder = direction;
                state.pendingOrderFrames = 1;
            } else {
                state.pendingOrderFrames++;
            }
            if (int(state.pendingOrderFrames) >= SIDE_CONFIRM_FRAMES) {
                state.stableY = markerY;
                state.order = markerY;
                state.pendingOrderFrames = 0;
            }
        }

        private function updateStableSide(item:Object,
                                          width:Number):String {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var state:Object = item.state;
            var bounds:Rectangle = item.avoidance as Rectangle;
            var centerX:Number = bounds.x + bounds.width * 0.5;
            var side:String = state.side as String;
            if (side != "left" && side != "right") {
                if (Number(item.markerX) < centerX - SIDE_HYSTERESIS) {
                    side = "left";
                } else if (Number(item.markerX) > centerX +
                           SIDE_HYSTERESIS) {
                    side = "right";
                } else {
                    side = prefersLeft(marker.pointId) ? "left" : "right";
                }
                state.side = side;
            }
            var opposite:String = side == "left" ? "right" : "left";
            if (!sideUsable(side, bounds, marker.calloutWidth, width) &&
                    sideUsable(opposite, bounds, marker.calloutWidth, width)) {
                state.side = opposite;
                state.pendingSide = null;
                state.pendingFrames = 0;
                return opposite;
            }
            var desired:String = side;
            if (Number(item.markerX) < centerX - SIDE_HYSTERESIS) {
                desired = "left";
            } else if (Number(item.markerX) > centerX + SIDE_HYSTERESIS) {
                desired = "right";
            }
            if (desired == side) {
                state.pendingSide = null;
                state.pendingFrames = 0;
                return side;
            }
            if (state.pendingSide != desired) {
                state.pendingSide = desired;
                state.pendingFrames = 1;
            } else {
                state.pendingFrames++;
            }
            if (int(state.pendingFrames) >= SIDE_CONFIRM_FRAMES) {
                state.side = desired;
                state.pendingSide = null;
                state.pendingFrames = 0;
                return desired;
            }
            return side;
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

        private function layoutTop(item:Object, bounds:Rectangle,
                                   width:Number, height:Number,
                                   smoothingAlpha:Number):Rectangle {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var boxX:Number = clamp(
                Number(item.markerX) - marker.calloutWidth * 0.5,
                SCREEN_MARGIN,
                Math.max(SCREEN_MARGIN,
                         width - SCREEN_MARGIN - marker.calloutWidth));
            var boxY:Number = clamp(
                bounds.top - EDGE_OFFSET - marker.calloutHeight,
                SCREEN_MARGIN,
                Math.max(SCREEN_MARGIN,
                         height - SCREEN_MARGIN - marker.calloutHeight));
            var placement:Object = {
                "x": boxX,
                "y": boxY,
                "placement": "top"
            };
            return applyPlacement(
                item, placement, smoothingAlpha, [], [bounds]);
        }

        private function layoutSide(items:Array, side:String,
                                    avoidanceBounds:Array, occupied:Array,
                                    width:Number, height:Number,
                                    smoothingAlpha:Number):void {
            if (items.length == 0) {
                return;
            }
            items.sort(compareStableOrder);
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
                var placement:Object = findSidePlacement(
                    item, chosenSide, Number(item.slotY), avoidanceBounds,
                    occupied, width, height);
                if (placement == null) {
                    chosenSide = side == "left" ? "right" : "left";
                    placement = findSidePlacement(
                        item, chosenSide, Number(item.slotY),
                        avoidanceBounds, occupied, width, height);
                    if (placement != null) {
                        item.state.side = chosenSide;
                        item.state.pendingSide = null;
                        item.state.pendingFrames = 0;
                    }
                }
                if (placement == null) {
                    chosenSide = side;
                    placement = sidePlacement(
                        item, chosenSide, Number(item.slotY),
                        avoidanceBounds, width, height, true);
                }
                occupied.push(applyPlacement(
                    item, placement, smoothingAlpha, occupied,
                    avoidanceBounds));
            }
        }

        private function compareStableOrder(a:Object, b:Object):Number {
            var difference:Number = Number(a.state.order) -
                                    Number(b.state.order);
            if (difference != 0) {
                return difference;
            }
            var aId:String = SpotPointMarker(a.marker).pointId;
            var bId:String = SpotPointMarker(b.marker).pointId;
            return aId < bId ? -1 : (aId == bId ? 0 : 1);
        }

        private function findSidePlacement(
                item:Object, side:String, desiredY:Number,
                avoidanceBounds:Array, occupied:Array,
                width:Number, height:Number):Object {
            for (var attempt:int = 0; attempt < MAX_SLOT_ATTEMPTS;
                    attempt++) {
                var distance:Number = Math.ceil(attempt * 0.5) * CALLOUT_GAP;
                var direction:Number = attempt == 0 ? 0 :
                    (attempt % 2 == 1 ? -1 : 1);
                var centerY:Number = desiredY + distance * direction;
                var placement:Object = sidePlacement(
                    item, side, centerY, avoidanceBounds,
                    width, height, false);
                if (placement != null && !overlapsLabels(
                        placement.rect as Rectangle, occupied)) {
                    return placement;
                }
            }
            return null;
        }

        private function sidePlacement(
                item:Object, side:String, centerY:Number,
                avoidanceBounds:Array, width:Number, height:Number,
                allowBlocked:Boolean):Object {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var halfHeight:Number = marker.calloutHeight * 0.5;
            centerY = clamp(
                centerY, SCREEN_MARGIN + halfHeight,
                height - SCREEN_MARGIN - halfHeight);
            var boxY:Number = centerY - halfHeight;
            var edgeX:Number = side == "left" ?
                Rectangle(item.avoidance).left - EDGE_OFFSET :
                Rectangle(item.avoidance).right + EDGE_OFFSET;
            for each (var bounds:Rectangle in avoidanceBounds) {
                if (boxY < bounds.bottom &&
                        boxY + marker.calloutHeight > bounds.top) {
                    edgeX = side == "left" ?
                        Math.min(edgeX, bounds.left - EDGE_OFFSET) :
                        Math.max(edgeX, bounds.right + EDGE_OFFSET);
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
            if (!allowBlocked) {
                for each (bounds in avoidanceBounds) {
                    if (rect.intersects(bounds)) {
                        return null;
                    }
                }
            }
            return {
                "x": boxX,
                "y": boxY,
                "placement": side,
                "rect": rect
            };
        }

        private function applyPlacement(
                item:Object, placement:Object, smoothingAlpha:Number,
                occupied:Array, avoidanceBounds:Array):Rectangle {
            var marker:SpotPointMarker = item.marker as SpotPointMarker;
            var state:Object = item.state;
            var targetX:Number = Number(placement.x);
            var targetY:Number = Number(placement.y);
            if (!Boolean(state.initialized)) {
                state.displayX = targetX;
                state.displayY = targetY;
                state.initialized = true;
            } else {
                if (Math.abs(targetX - Number(state.displayX)) >
                        POSITION_DEADBAND) {
                    state.displayX += (targetX - Number(state.displayX)) *
                                      smoothingAlpha;
                }
                if (Math.abs(targetY - Number(state.displayY)) >
                        POSITION_DEADBAND) {
                    state.displayY += (targetY - Number(state.displayY)) *
                                      smoothingAlpha;
                }
            }
            var displayed:Rectangle = new Rectangle(
                Number(state.displayX), Number(state.displayY),
                marker.calloutWidth, marker.calloutHeight);
            if (isBlocked(displayed, occupied, avoidanceBounds)) {
                state.displayX = targetX;
                state.displayY = targetY;
                displayed.x = targetX;
                displayed.y = targetY;
            }
            marker.layoutCallout(
                displayed.x, displayed.y, String(placement.placement));
            return displayed;
        }

        private function isBlocked(rect:Rectangle, occupied:Array,
                                   avoidanceBounds:Array):Boolean {
            for each (var bounds:Rectangle in avoidanceBounds) {
                if (rect.intersects(bounds)) {
                    return true;
                }
            }
            return overlapsLabels(rect, occupied);
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

        private function resetLayoutState():void {
            layoutStates = new Dictionary();
            lastLayoutTime = 0;
        }

        private function removeMarker(id:String):void {
            var marker:SpotPointMarker = markers[id] as SpotPointMarker;
            if (marker == null) {
                return;
            }
            removeChild(marker);
            marker.dispose();
            delete markers[id];
            delete layoutStates[id];
        }

        override protected function onBeforeDispose():void {
            removeEventListener(Event.ENTER_FRAME, onEnterFrame);
            as_clearMarkers();
            super.onBeforeDispose();
        }

        override protected function onDispose():void {
            markers = null;
            layoutAnchors = null;
            layoutStates = null;
            super.onDispose();
        }
    }
}
