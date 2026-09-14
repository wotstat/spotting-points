package wotstat.spottingpoints {
    import flash.geom.Point;
    import flash.geom.Rectangle;

    public final class LayoutGeometry {
        private static const EPSILON:Number = 0.0001;
        private static const INFLATE_SIDES:int = 8;
        private static const INFLATE_RADIUS_SCALE:Number =
            1.082392200292394;

        public static function convexHull(input:Array):Array {
            var sorted:Array = [];
            for each (var inputPoint:Point in input) {
                if (inputPoint != null) {
                    sorted.push(new Point(inputPoint.x, inputPoint.y));
                }
            }
            sorted.sort(comparePoints);

            var points:Array = [];
            for each (var point:Point in sorted) {
                if (points.length == 0 || !samePoint(
                        points[points.length - 1] as Point, point)) {
                    points.push(point);
                }
            }
            if (points.length <= 2) {
                return points;
            }

            var lower:Array = [];
            for each (point in points) {
                while (lower.length >= 2 && cross(
                        lower[lower.length - 2] as Point,
                        lower[lower.length - 1] as Point,
                        point) <= EPSILON) {
                    lower.pop();
                }
                lower.push(point);
            }

            var upper:Array = [];
            for (var index:int = points.length - 1; index >= 0; index--) {
                point = points[index] as Point;
                while (upper.length >= 2 && cross(
                        upper[upper.length - 2] as Point,
                        upper[upper.length - 1] as Point,
                        point) <= EPSILON) {
                    upper.pop();
                }
                upper.push(point);
            }
            lower.pop();
            upper.pop();
            return lower.concat(upper);
        }

        public static function inflateConvexPolygon(
                points:Array, padding:Number):Array {
            if (points == null || points.length == 0 || padding <= 0) {
                return points == null ? [] : points.concat();
            }
            var cloud:Array = [];
            var radius:Number = padding * INFLATE_RADIUS_SCALE;
            for each (var point:Point in points) {
                for (var index:int = 0; index < INFLATE_SIDES; index++) {
                    var angle:Number = Math.PI * 2 * index / INFLATE_SIDES;
                    cloud.push(new Point(
                        point.x + Math.cos(angle) * radius,
                        point.y + Math.sin(angle) * radius));
                }
            }
            return convexHull(cloud);
        }

        public static function polygonBounds(points:Array):Rectangle {
            if (points == null || points.length == 0) {
                return null;
            }
            var minX:Number = Number.POSITIVE_INFINITY;
            var minY:Number = Number.POSITIVE_INFINITY;
            var maxX:Number = Number.NEGATIVE_INFINITY;
            var maxY:Number = Number.NEGATIVE_INFINITY;
            for each (var point:Point in points) {
                minX = Math.min(minX, point.x);
                minY = Math.min(minY, point.y);
                maxX = Math.max(maxX, point.x);
                maxY = Math.max(maxY, point.y);
            }
            return new Rectangle(minX, minY, maxX - minX, maxY - minY);
        }

        public static function horizontalSpan(points:Array, minY:Number,
                                              maxY:Number):Object {
            if (points == null || points.length < 3) {
                return null;
            }
            var values:Array = [];
            for each (var point:Point in points) {
                if (point.y >= minY - EPSILON &&
                        point.y <= maxY + EPSILON) {
                    values.push(point.x);
                }
            }
            addHorizontalIntersections(points, minY, values);
            if (Math.abs(maxY - minY) > EPSILON) {
                addHorizontalIntersections(points, maxY, values);
            }
            return range(values);
        }

        public static function verticalSpan(points:Array, minX:Number,
                                            maxX:Number):Object {
            if (points == null || points.length < 3) {
                return null;
            }
            var values:Array = [];
            for each (var point:Point in points) {
                if (point.x >= minX - EPSILON &&
                        point.x <= maxX + EPSILON) {
                    values.push(point.y);
                }
            }
            addVerticalIntersections(points, minX, values);
            if (Math.abs(maxX - minX) > EPSILON) {
                addVerticalIntersections(points, maxX, values);
            }
            return range(values);
        }

        public static function rectangleIntersectsPolygon(
                rect:Rectangle, points:Array):Boolean {
            if (points == null || points.length < 3) {
                return false;
            }
            for each (var point:Point in points) {
                if (containsInclusive(rect, point)) {
                    return true;
                }
            }

            var corners:Array = [
                new Point(rect.left, rect.top),
                new Point(rect.right, rect.top),
                new Point(rect.right, rect.bottom),
                new Point(rect.left, rect.bottom)
            ];
            for each (point in corners) {
                if (pointInPolygon(point, points)) {
                    return true;
                }
            }

            for (var index:int = 0; index < points.length; index++) {
                var start:Point = points[index] as Point;
                var end:Point = points[(index + 1) % points.length] as Point;
                for (var edge:int = 0; edge < corners.length; edge++) {
                    if (segmentsIntersect(
                            start, end,
                            corners[edge] as Point,
                            corners[(edge + 1) % corners.length] as Point)) {
                        return true;
                    }
                }
            }
            return false;
        }

        private static function addHorizontalIntersections(
                points:Array, y:Number, values:Array):void {
            for (var index:int = 0; index < points.length; index++) {
                var start:Point = points[index] as Point;
                var end:Point = points[(index + 1) % points.length] as Point;
                if (y < Math.min(start.y, end.y) - EPSILON ||
                        y > Math.max(start.y, end.y) + EPSILON ||
                        Math.abs(end.y - start.y) <= EPSILON) {
                    continue;
                }
                var ratio:Number = (y - start.y) / (end.y - start.y);
                values.push(start.x + (end.x - start.x) * ratio);
            }
        }

        private static function addVerticalIntersections(
                points:Array, x:Number, values:Array):void {
            for (var index:int = 0; index < points.length; index++) {
                var start:Point = points[index] as Point;
                var end:Point = points[(index + 1) % points.length] as Point;
                if (x < Math.min(start.x, end.x) - EPSILON ||
                        x > Math.max(start.x, end.x) + EPSILON ||
                        Math.abs(end.x - start.x) <= EPSILON) {
                    continue;
                }
                var ratio:Number = (x - start.x) / (end.x - start.x);
                values.push(start.y + (end.y - start.y) * ratio);
            }
        }

        private static function range(values:Array):Object {
            if (values.length == 0) {
                return null;
            }
            var minimum:Number = Number.POSITIVE_INFINITY;
            var maximum:Number = Number.NEGATIVE_INFINITY;
            for each (var value:Number in values) {
                minimum = Math.min(minimum, value);
                maximum = Math.max(maximum, value);
            }
            return {"min": minimum, "max": maximum};
        }

        private static function pointInPolygon(point:Point,
                                               points:Array):Boolean {
            var inside:Boolean = false;
            var previous:int = points.length - 1;
            for (var index:int = 0; index < points.length; index++) {
                var currentPoint:Point = points[index] as Point;
                var previousPoint:Point = points[previous] as Point;
                if (pointOnSegment(point, previousPoint, currentPoint)) {
                    return true;
                }
                if ((currentPoint.y > point.y) !=
                        (previousPoint.y > point.y) &&
                        point.x < (previousPoint.x - currentPoint.x) *
                        (point.y - currentPoint.y) /
                        (previousPoint.y - currentPoint.y) + currentPoint.x) {
                    inside = !inside;
                }
                previous = index;
            }
            return inside;
        }

        private static function segmentsIntersect(a:Point, b:Point,
                                                  c:Point, d:Point):Boolean {
            var abC:Number = cross(a, b, c);
            var abD:Number = cross(a, b, d);
            var cdA:Number = cross(c, d, a);
            var cdB:Number = cross(c, d, b);
            if (((abC > EPSILON && abD < -EPSILON) ||
                    (abC < -EPSILON && abD > EPSILON)) &&
                    ((cdA > EPSILON && cdB < -EPSILON) ||
                    (cdA < -EPSILON && cdB > EPSILON))) {
                return true;
            }
            return (Math.abs(abC) <= EPSILON && pointOnSegment(c, a, b)) ||
                (Math.abs(abD) <= EPSILON && pointOnSegment(d, a, b)) ||
                (Math.abs(cdA) <= EPSILON && pointOnSegment(a, c, d)) ||
                (Math.abs(cdB) <= EPSILON && pointOnSegment(b, c, d));
        }

        private static function pointOnSegment(point:Point, start:Point,
                                               end:Point):Boolean {
            return Math.abs(cross(start, end, point)) <= EPSILON &&
                point.x >= Math.min(start.x, end.x) - EPSILON &&
                point.x <= Math.max(start.x, end.x) + EPSILON &&
                point.y >= Math.min(start.y, end.y) - EPSILON &&
                point.y <= Math.max(start.y, end.y) + EPSILON;
        }

        private static function containsInclusive(rect:Rectangle,
                                                  point:Point):Boolean {
            return point.x >= rect.left - EPSILON &&
                point.x <= rect.right + EPSILON &&
                point.y >= rect.top - EPSILON &&
                point.y <= rect.bottom + EPSILON;
        }

        private static function comparePoints(a:Point, b:Point):Number {
            if (Math.abs(a.x - b.x) > EPSILON) {
                return a.x - b.x;
            }
            return a.y - b.y;
        }

        private static function samePoint(a:Point, b:Point):Boolean {
            return Math.abs(a.x - b.x) <= EPSILON &&
                Math.abs(a.y - b.y) <= EPSILON;
        }

        private static function cross(origin:Point, a:Point,
                                      b:Point):Number {
            return (a.x - origin.x) * (b.y - origin.y) -
                (a.y - origin.y) * (b.x - origin.x);
        }
    }
}
