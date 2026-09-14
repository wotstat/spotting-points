package wotstat.spottingpoints {
    import flash.display.Sprite;
    import flash.geom.Point;
    import flash.geom.Rectangle;

    public class LayoutDebugOverlay extends Sprite {
        private static const HULL_COLOR:uint = 0xFF9B3D;
        private static const TURRET_COLOR:uint = 0x38CCFF;
        private static const BLOCKED_COLOR:uint = 0xFF365E;
        private static const SELECTED_COLOR:uint = 0xFFE066;

        private static const BOX_EDGES:Array = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7]
        ];

        public function LayoutDebugOverlay() {
            super();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function render(hullPart:Object, turretPart:Object,
                               placements:Array):void {
            graphics.clear();
            if (!visible || hullPart == null || turretPart == null) {
                return;
            }

            drawBlockedPolygon(hullPart.obstacle as Array);
            drawBlockedPolygon(turretPart.obstacle as Array);
            drawProjectedBox(hullPart, HULL_COLOR);
            drawProjectedBox(turretPart, TURRET_COLOR);
            drawSelectedPlacements(placements);
        }

        public function clear():void {
            graphics.clear();
        }

        private function drawBlockedPolygon(points:Array):void {
            if (points == null || points.length < 3) {
                return;
            }
            graphics.lineStyle(2, BLOCKED_COLOR, 0.82);
            graphics.beginFill(BLOCKED_COLOR, 0.055);
            var first:Point = points[0] as Point;
            graphics.moveTo(first.x, first.y);
            for (var index:int = 1; index < points.length; index++) {
                var point:Point = points[index] as Point;
                graphics.lineTo(point.x, point.y);
            }
            graphics.lineTo(first.x, first.y);
            graphics.endFill();
        }

        private function drawProjectedBox(part:Object, color:uint):void {
            if (part == null || part.points == null ||
                    part.points.length != 8) {
                return;
            }
            var points:Array = part.points as Array;
            graphics.lineStyle(1.5, color, 0.92);
            for each (var edge:Array in BOX_EDGES) {
                var start:Point = points[int(edge[0])] as Point;
                var end:Point = points[int(edge[1])] as Point;
                graphics.moveTo(start.x, start.y);
                graphics.lineTo(end.x, end.y);
            }
            for each (var point:Point in points) {
                graphics.beginFill(color, 0.96);
                graphics.drawCircle(point.x, point.y, 2.5);
                graphics.endFill();
            }
        }

        private function drawSelectedPlacements(placements:Array):void {
            if (placements == null) {
                return;
            }
            graphics.lineStyle(2, SELECTED_COLOR, 0.9);
            for each (var entry:Object in placements) {
                var placement:Object = entry.placement;
                var rect:Rectangle = placement != null ?
                    placement.rect as Rectangle : null;
                if (rect == null) {
                    continue;
                }
                graphics.drawRoundRect(
                    rect.x, rect.y, rect.width, rect.height, 5, 5);
            }
        }
    }
}
