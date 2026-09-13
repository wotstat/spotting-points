package wotstat.spottingpoints {
    import flash.display.DisplayObject;
    import flash.events.Event;
    import flash.geom.Point;
    import flash.utils.Dictionary;
    import net.wg.infrastructure.base.AbstractView;

    public class MarkerOverlay extends AbstractView {
        private static const CALLOUT_GAP:Number = 28;
        private static const EDGE_OFFSET:Number = 34;
        private static const SCREEN_MARGIN:Number = 8;

        private var markers:Dictionary = new Dictionary();
        private var active:Boolean = true;

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
            var minX:Number = width;
            var maxX:Number = 0;
            var centerX:Number = 0;
            var centerCount:int = 0;
            var left:Array = [];
            var right:Array = [];
            var marker:SpotPointMarker;
            for each (marker in markers) {
                if (!marker.visible) {
                    continue;
                }
                visibleMarkers.push(marker);
                var position:Point = markerPosition(marker);
                minX = Math.min(minX, position.x);
                maxX = Math.max(maxX, position.x);
                if (isBodyPoint(marker.pointId)) {
                    centerX += position.x;
                    centerCount++;
                }
            }
            if (visibleMarkers.length == 0) {
                return;
            }
            centerX = centerCount > 0 ? centerX / centerCount : width * 0.5;
            for each (marker in visibleMarkers) {
                if (!marker.isCalloutVisible) {
                    continue;
                }
                position = markerPosition(marker);
                var placeLeft:Boolean = chooseLeft(
                    marker, position.x, centerX);
                var item:Object = {
                    "marker": marker,
                    "markerX": position.x,
                    "markerY": position.y,
                    "desiredY": position.y,
                    "placeLeft": placeLeft
                };
                (placeLeft ? left : right).push(item);
            }
            layoutSide(left, true, minX, maxX, width, height);
            layoutSide(right, false, minX, maxX, width, height);
        }

        private function markerPosition(marker:SpotPointMarker):Point {
            return globalToLocal(marker.localToGlobal(new Point(0, 0)));
        }

        private function chooseLeft(marker:SpotPointMarker, markerX:Number,
                                    centerX:Number):Boolean {
            if (Math.abs(markerX - centerX) > 12) {
                return markerX < centerX;
            }
            return marker.pointId == "rear" ||
                   marker.pointId == "gunStatic" ||
                   marker.pointId == "left";
        }

        private function isBodyPoint(pointId:String):Boolean {
            return pointId == "rear" || pointId == "front" ||
                   pointId == "left" || pointId == "right";
        }

        private function layoutSide(items:Array, placeLeft:Boolean,
                                    minX:Number, maxX:Number,
                                    width:Number, height:Number):void {
            if (items.length == 0) {
                return;
            }
            for each (var item:Object in items) {
                var marker:SpotPointMarker = item.marker as SpotPointMarker;
                var edgeX:Number;
                if (placeLeft) {
                    edgeX = Math.max(minX - EDGE_OFFSET,
                        marker.calloutWidth + SCREEN_MARGIN);
                } else {
                    edgeX = Math.min(maxX + EDGE_OFFSET,
                        width - marker.calloutWidth - SCREEN_MARGIN);
                }
                item.edgeX = edgeX;
                item.distance = Math.abs(Number(item.markerX) - edgeX);
            }
            items.sortOn("distance", Array.NUMERIC);
            var placed:Array = [];
            for each (item in items) {
                item.layoutY = findNearestLayoutY(item, placed, height, true);
                if (isNaN(Number(item.layoutY))) {
                    item.layoutY = findNearestLayoutY(
                        item, placed, height, false);
                }
                placed.push(item);
            }
            for each (item in items) {
                marker = item.marker as SpotPointMarker;
                marker.layoutCallout(
                    Number(item.edgeX), Number(item.layoutY), placeLeft);
            }
        }

        private function findNearestLayoutY(item:Object, placed:Array,
                                            height:Number,
                                            avoidCrossing:Boolean):Number {
            var minimum:Number = SCREEN_MARGIN + CALLOUT_GAP * 0.5;
            var maximum:Number = height - SCREEN_MARGIN - CALLOUT_GAP * 0.5;
            var desired:Number = Math.max(minimum,
                Math.min(maximum, Number(item.desiredY)));
            var candidates:Array = [desired];
            for each (var occupied:Object in placed) {
                candidates.push(Number(occupied.layoutY) - CALLOUT_GAP);
                candidates.push(Number(occupied.layoutY) + CALLOUT_GAP);
            }
            candidates.sort(function(a:Number, b:Number):Number {
                var distanceA:Number = Math.abs(a - desired);
                var distanceB:Number = Math.abs(b - desired);
                if (distanceA == distanceB) {
                    return a - b;
                }
                return distanceA - distanceB;
            });
            for each (var candidate:Number in candidates) {
                if (candidate < minimum || candidate > maximum ||
                        !hasVerticalSpace(candidate, placed)) {
                    continue;
                }
                if (!avoidCrossing ||
                        !crossesPlacedConnector(item, candidate, placed)) {
                    return candidate;
                }
            }
            return NaN;
        }

        private function hasVerticalSpace(candidate:Number,
                                          placed:Array):Boolean {
            for each (var item:Object in placed) {
                if (Math.abs(candidate - Number(item.layoutY)) <
                        CALLOUT_GAP - 0.1) {
                    return false;
                }
            }
            return true;
        }

        private function crossesPlacedConnector(item:Object,
                                                 candidate:Number,
                                                 placed:Array):Boolean {
            for each (var other:Object in placed) {
                if (segmentsCross(
                        Number(item.markerX), Number(item.markerY),
                        Number(item.edgeX), candidate,
                        Number(other.markerX), Number(other.markerY),
                        Number(other.edgeX), Number(other.layoutY))) {
                    return true;
                }
            }
            return false;
        }

        private function segmentsCross(ax:Number, ay:Number,
                                       bx:Number, by:Number,
                                       cx:Number, cy:Number,
                                       dx:Number, dy:Number):Boolean {
            var abC:Number = cross(ax, ay, bx, by, cx, cy);
            var abD:Number = cross(ax, ay, bx, by, dx, dy);
            var cdA:Number = cross(cx, cy, dx, dy, ax, ay);
            var cdB:Number = cross(cx, cy, dx, dy, bx, by);
            return abC * abD < 0 && cdA * cdB < 0;
        }

        private function cross(ax:Number, ay:Number, bx:Number, by:Number,
                               cx:Number, cy:Number):Number {
            return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
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
            super.onDispose();
        }
    }
}
