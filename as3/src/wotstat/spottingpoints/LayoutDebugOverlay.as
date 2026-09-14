package wotstat.spottingpoints {
    import flash.display.Sprite;

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

        public function render(result:Object):void {
            graphics.clear();
            if (!visible || result == null || result.hull == null ||
                    result.turret == null) {
                return;
            }
            drawBlockedPolygon(result.hull.obstacle as Array);
            drawBlockedPolygon(result.turret.obstacle as Array);
            drawProjectedBox(result.hull.points as Array, HULL_COLOR);
            drawProjectedBox(result.turret.points as Array, TURRET_COLOR);
            drawSelectedPlacements(result.placements as Array);
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
            graphics.moveTo(pointX(points[0]), pointY(points[0]));
            for (var index:int = 1; index < points.length; index++) {
                graphics.lineTo(pointX(points[index]), pointY(points[index]));
            }
            graphics.lineTo(pointX(points[0]), pointY(points[0]));
            graphics.endFill();
        }

        private function drawProjectedBox(points:Array, color:uint):void {
            if (points == null || points.length != 8) {
                return;
            }
            graphics.lineStyle(1.5, color, 0.92);
            for each (var edge:Array in BOX_EDGES) {
                var start:Object = points[int(edge[0])];
                var end:Object = points[int(edge[1])];
                graphics.moveTo(pointX(start), pointY(start));
                graphics.lineTo(pointX(end), pointY(end));
            }
            for each (var point:Object in points) {
                graphics.beginFill(color, 0.96);
                graphics.drawCircle(pointX(point), pointY(point), 2.5);
                graphics.endFill();
            }
        }

        private function drawSelectedPlacements(placements:Array):void {
            if (placements == null) {
                return;
            }
            graphics.lineStyle(2, SELECTED_COLOR, 0.9);
            for each (var placement:Object in placements) {
                var rect:Array = placement.rect as Array;
                if (rect != null && rect.length == 4) {
                    graphics.drawRoundRect(
                        Number(rect[0]), Number(rect[1]),
                        Number(rect[2]), Number(rect[3]), 5, 5);
                }
                var leader:Array = placement.leader as Array;
                if (leader == null || leader.length < 2) {
                    continue;
                }
                graphics.moveTo(pointX(leader[0]), pointY(leader[0]));
                for (var index:int = 1; index < leader.length; index++) {
                    graphics.lineTo(
                        pointX(leader[index]), pointY(leader[index]));
                }
            }
        }

        private function pointX(value:Object):Number {
            return Number(value[0]);
        }

        private function pointY(value:Object):Number {
            return Number(value[1]);
        }
    }
}
