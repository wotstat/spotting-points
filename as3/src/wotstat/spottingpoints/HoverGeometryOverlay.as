package wotstat.spottingpoints {
    import flash.display.DisplayObject;
    import flash.display.Sprite;
    import flash.geom.Point;
    import flash.utils.Dictionary;

    public class HoverGeometryOverlay extends Sprite {
        private static const FADED_COLOR:uint = 0x9AAFC4;
        private static const BRIGHT_COLOR:uint = 0x78B7FF;
        private static const FADED_ALPHA:Number = 0.46;
        private static const BRIGHT_ALPHA:Number = 0.98;
        private static const PROJECTION_ORIGIN_EPSILON:Number = 0.5;

        public function HoverGeometryOverlay() {
            super();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function render(lines:Array, anchors:Dictionary):void {
            graphics.clear();
            if (!visible || lines == null || anchors == null) {
                return;
            }
            for each (var line:Object in lines) {
                drawLine(line, anchors);
            }
        }

        public function clear():void {
            graphics.clear();
        }

        private function drawLine(line:Object, anchors:Dictionary):void {
            if (line == null || line.points == null) {
                return;
            }
            var ids:Array = line.points as Array;
            if (ids == null || ids.length < 2) {
                return;
            }
            var bright:Boolean = String(line.style) == "bright";
            graphics.lineStyle(bright ? 2.25 : 1.5,
                               bright ? BRIGHT_COLOR : FADED_COLOR,
                               bright ? BRIGHT_ALPHA : FADED_ALPHA);
            var drawing:Boolean = false;
            for (var index:int = 0; index < ids.length; index++) {
                var point:Point = projectedPoint(
                    anchors[String(ids[index])]);
                if (!validPoint(point)) {
                    drawing = false;
                    continue;
                }
                if (!drawing) {
                    graphics.moveTo(point.x, point.y);
                    drawing = true;
                } else {
                    graphics.lineTo(point.x, point.y);
                }
            }
        }

        private function projectedPoint(value:Object):Point {
            var anchor:DisplayObject = value as DisplayObject;
            if (anchor == null) {
                return null;
            }
            return globalToLocal(anchor.localToGlobal(new Point(0, 0)));
        }

        private function validPoint(point:Point):Boolean {
            return point != null && !isNaN(point.x) && !isNaN(point.y) &&
                   isFinite(point.x) && isFinite(point.y) &&
                   (Math.abs(point.x) > PROJECTION_ORIGIN_EPSILON ||
                    Math.abs(point.y) > PROJECTION_ORIGIN_EPSILON);
        }
    }
}
