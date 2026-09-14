package wotstat.spottingpoints {
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.geom.Point;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;
    import net.wg.infrastructure.base.AbstractView;

    public class MarkerOverlay extends AbstractView {
        public var solveLayout:Function;

        private var markers:Dictionary = new Dictionary();
        private var layoutAnchors:Dictionary = new Dictionary();
        private var debugOverlay:LayoutDebugOverlay;
        private var layoutDebug:Boolean = false;
        private var active:Boolean = true;
        private var calloutsEnabled:Boolean = true;
        private var lastLayoutRevision:Number = -1;
        private var lastLayoutResult:Object;

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
            marker.setCalloutsEnabled(calloutsEnabled);
            markers[id] = marker;
            addChild(marker);
            if (!marker.isObservationPoint) {
                setChildIndex(marker, debugOverlay != null ? 1 : 0);
            }
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
            for (var index:int = numChildren - 1; index >= 0; index--) {
                var marker:SpotPointMarker = getChildAt(index) as SpotPointMarker;
                if (marker != null && marker.visible && marker.hitTestUi(stageX, stageY)) {
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
            if (debugOverlay == null) {
                return;
            }
            debugOverlay.visible = value;
            if (value && lastLayoutResult != null) {
                debugOverlay.render(lastLayoutResult);
            } else if (!value) {
                debugOverlay.clear();
            }
        }

        public function as_setCalloutsEnabled(value:Boolean):void {
            calloutsEnabled = value;
            for each (var marker:SpotPointMarker in markers) {
                marker.setCalloutsEnabled(value);
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
            lastLayoutRevision = -1;
            lastLayoutResult = null;
            if (debugOverlay != null) {
                debugOverlay.clear();
            }
        }

        public function as_removeMarker(id:String):void {
            removeMarker(id);
        }

        private function onEnterFrame(event:Event):void {
            if (active) {
                var now:Number = getTimer();
                for each (var marker:SpotPointMarker in markers) {
                    marker.updatePulse(now);
                }
                layoutCallouts();
            }
        }

        private function layoutCallouts():void {
            if (solveLayout == null) {
                return;
            }
            var width:Number = App.appWidth;
            var height:Number = App.appHeight;
            if (width <= 0 || height <= 0) {
                return;
            }
            var hull:Array = projectedPoints("hull");
            var turret:Array = projectedPoints("turret");
            if (hull == null || turret == null) {
                return;
            }

            var items:Array = [];
            for each (var marker:SpotPointMarker in markers) {
                if (!marker.visible || !marker.isCalloutVisible) {
                    continue;
                }
                var position:Point = displayPosition(marker);
                if (!validPoint(position)) {
                    return;
                }
                items.push({
                    "id": marker.pointId,
                    "x": position.x,
                    "y": position.y,
                    "width": marker.calloutWidth,
                    "height": marker.calloutHeight,
                    "part": isTurretPoint(marker.pointId) ?
                        "turret" : "hull"
                });
            }
            items.sort(compareItems);

            var result:Object = solveLayout({
                "width": width,
                "height": height,
                "hull": hull,
                "turret": turret,
                "items": items
            });
            if (result == null || Boolean(result.disabled)) {
                return;
            }
            var revision:Number = Number(result.revision);
            if (!isFinite(revision) || revision == lastLayoutRevision ||
                    result.placements == null) {
                return;
            }
            var placements:Array = result.placements as Array;
            if (placements == null || placements.length != items.length ||
                    !applyLayoutResult(placements)) {
                return;
            }
            lastLayoutRevision = revision;
            lastLayoutResult = result;
            if (debugOverlay != null && layoutDebug) {
                debugOverlay.render(result);
            }
        }

        private function projectedPoints(prefix:String):Array {
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
                points.push([point.x, point.y]);
            }
            return points;
        }

        private function applyLayoutResult(placements:Array):Boolean {
            for each (var placement:Object in placements) {
                var marker:SpotPointMarker = markers[
                    String(placement.id)] as SpotPointMarker;
                var rect:Array = placement.rect as Array;
                var leader:Array = placement.leader as Array;
                if (marker == null || rect == null || rect.length != 4 ||
                        leader == null || leader.length < 2) {
                    return false;
                }
            }
            for each (placement in placements) {
                marker = markers[String(placement.id)] as SpotPointMarker;
                rect = placement.rect as Array;
                marker.layoutCallout(
                    Number(rect[0]), Number(rect[1]),
                    placement.leader as Array);
            }
            return true;
        }

        private function displayPosition(value:DisplayObject):Point {
            return globalToLocal(value.localToGlobal(new Point(0, 0)));
        }

        private function validPoint(point:Point):Boolean {
            return point != null && !isNaN(point.x) && !isNaN(point.y) &&
                   isFinite(point.x) && isFinite(point.y);
        }

        private function isTurretPoint(pointId:String):Boolean {
            return pointId == "gunStatic" || pointId == "gunMoving";
        }

        private function compareItems(first:Object, second:Object):Number {
            var firstId:String = String(first.id);
            var secondId:String = String(second.id);
            return firstId < secondId ? -1 :
                (firstId == secondId ? 0 : 1);
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
            solveLayout = null;
            super.onDispose();
        }
    }
}
