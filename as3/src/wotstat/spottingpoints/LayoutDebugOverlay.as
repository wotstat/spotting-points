package wotstat.spottingpoints {
    import flash.display.Sprite;
    import flash.geom.Point;
    import flash.geom.Rectangle;

    public class LayoutDebugOverlay extends Sprite {
        private static const HULL_COLOR:uint = 0xFF9B3D;
        private static const TURRET_COLOR:uint = 0x38CCFF;
        private static const BLOCKED_COLOR:uint = 0xFF365E;
        private static const AVAILABLE_COLOR:uint = 0x39E68A;
        private static const SELECTED_COLOR:uint = 0xFFE066;
        private static const SCREEN_MARGIN:Number = 8;

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
                               candidates:Array, placements:Array,
                               width:Number, height:Number):void {
            graphics.clear();
            if (!visible || hullPart == null || turretPart == null) {
                return;
            }

            drawSafeScreen(width, height);
            drawCandidates(candidates);
            drawBlockedPolygon(hullPart.obstacle as Array);
            drawBlockedPolygon(turretPart.obstacle as Array);
            drawProjectedBox(hullPart, HULL_COLOR);
            drawProjectedBox(turretPart, TURRET_COLOR);
            drawSelectedPlacements(placements);
        }

        public function clear():void {
            graphics.clear();
        }

        private function drawSafeScreen(width:Number, height:Number):void {
            graphics.lineStyle(1, AVAILABLE_COLOR, 0.28);
            graphics.drawRect(
                SCREEN_MARGIN, SCREEN_MARGIN,
                Math.max(0, width - SCREEN_MARGIN * 2),
                Math.max(0, height - SCREEN_MARGIN * 2));
        }

        private function drawCandidates(candidates:Array):void {
            if (candidates == null) {
                return;
            }
            var byKey:Object = {};
            var keys:Array = [];
            for each (var candidate:Object in candidates) {
                var rect:Rectangle = candidate.rect as Rectangle;
                if (rect == null) {
                    continue;
                }
                var key:String = candidateKey(candidate, rect);
                var previous:Object = byKey[key];
                if (previous == null) {
                    byKey[key] = candidate;
                    keys.push(key);
                } else if (Boolean(candidate.valid) &&
                           !Boolean(previous.valid)) {
                    byKey[key] = candidate;
                }
            }
            keys.sort();
            for each (key in keys) {
                candidate = byKey[key];
                rect = candidate.rect as Rectangle;
                drawCandidateRect(rect, Boolean(candidate.valid));
            }
        }

        private function candidateKey(candidate:Object,
                                      rect:Rectangle):String {
            return String(candidate.placement) + ":" +
                String(candidate.pointId) + ":" +
                Math.round(rect.x * 2) + ":" +
                Math.round(rect.y * 2) + ":" +
                Math.round(rect.width * 2) + ":" +
                Math.round(rect.height * 2);
        }

        private function drawCandidateRect(rect:Rectangle,
                                           valid:Boolean):void {
            var color:uint = valid ? AVAILABLE_COLOR : BLOCKED_COLOR;
            graphics.lineStyle(1, color, valid ? 0.55 : 0.25);
            graphics.beginFill(color, valid ? 0.035 : 0.018);
            graphics.drawRoundRect(
                rect.x, rect.y, rect.width, rect.height, 5, 5);
            graphics.endFill();
            if (!valid) {
                graphics.moveTo(rect.x + 3, rect.y + 3);
                graphics.lineTo(rect.right - 3, rect.bottom - 3);
                graphics.moveTo(rect.right - 3, rect.y + 3);
                graphics.lineTo(rect.x + 3, rect.bottom - 3);
            }
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
