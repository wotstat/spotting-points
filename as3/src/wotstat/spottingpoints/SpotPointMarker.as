package wotstat.spottingpoints {
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.filters.GlowFilter;
    import flash.geom.Point;
    import flash.text.AntiAliasType;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;
    import flash.utils.getTimer;

    public class SpotPointMarker extends Sprite {
        private static const DOT_RADIUS:Number = 4;
        private static const CALLOUT_HEIGHT:Number = 24;
        private static const CALLOUT_PADDING:Number = 8;
        private static const CALLOUT_TEXT_Y:Number = 1;
        private static const PULSE_DURATION:Number = 850;
        private static const PULSE_DELAY:Number = 1750;

        public var pointId:String;

        private var dot:Shape;
        private var ring:Shape;
        private var connector:Shape;
        private var callout:Sprite;
        private var calloutBackground:Shape;
        private var labelField:TextField;
        private var persistentCallout:Boolean = false;
        private var hovered:Boolean = false;
        private var calloutsEnabled:Boolean = true;
        private var currentLabel:String = "";

        public function SpotPointMarker(id:String, label:String) {
            super();
            pointId = id;
            mouseEnabled = false;
            mouseChildren = false;

            connector = new Shape();
            connector.filters = [
                new GlowFilter(0x000000, 0.65, 16, 16, 1.5, 3)
            ];
            addChild(connector);

            ring = new Shape();
            ring.graphics.lineStyle(1.5, 0xFFF2B2, 0.72);
            if (isObservationPoint) {
                ring.graphics.drawRect(-6, -6, 12, 12);
                ring.rotation = 45;
            } else {
                ring.graphics.drawCircle(0, 0, DOT_RADIUS + 2);
            }
            ring.alpha = 0.72;
            addChild(ring);

            dot = new Shape();
            dot.graphics.lineStyle(2, 0xFFF5C9, 1);
            dot.graphics.beginFill(0x22252A, 0.96);
            if (isObservationPoint) {
                dot.graphics.drawRect(-DOT_RADIUS, -DOT_RADIUS,
                                      DOT_RADIUS * 2, DOT_RADIUS * 2);
                dot.rotation = 45;
            } else {
                dot.graphics.drawCircle(0, 0, DOT_RADIUS);
            }
            dot.graphics.endFill();
            addChild(dot);

            callout = new Sprite();
            // Keep it measurable for layout, but hidden until positioned.
            callout.alpha = 0;
            calloutBackground = new Shape();
            callout.addChild(calloutBackground);
            labelField = new TextField();
            labelField.antiAliasType = AntiAliasType.ADVANCED;
            labelField.autoSize = TextFieldAutoSize.LEFT;
            labelField.defaultTextFormat = new TextFormat(
                "$FieldFont", 13, 0xF4F4F4);
            labelField.mouseEnabled = false;
            labelField.selectable = false;
            labelField.x = CALLOUT_PADDING;
            labelField.y = CALLOUT_TEXT_Y;
            callout.addChild(labelField);
            addChild(callout);
            setLabel(label);
            updateCalloutVisibility();

            updatePulse(getTimer());
        }

        public function updatePulse(now:Number):void {
            var phase:Number = now % (PULSE_DELAY + PULSE_DURATION);
            ring.visible = phase >= PULSE_DELAY;
            var progress:Number = Math.max(0, (phase - PULSE_DELAY) / PULSE_DURATION);
            ring.alpha = 0.72 * (1 - progress);
            ring.scaleX = ring.scaleY = 1 + 1.6 * progress;
        }

        public function setData(label:String, showCallout:Boolean):void {
            setLabel(label);
            persistentCallout = showCallout;
            updateCalloutVisibility();
        }

        public function get isObservationPoint():Boolean {
            return pointId == "top" || pointId == "gunMoving";
        }

        public function setHovered(value:Boolean):void {
            hovered = value;
            updateCalloutVisibility();
        }

        public function setCalloutsEnabled(value:Boolean):void {
            calloutsEnabled = value;
            updateCalloutVisibility();
        }

        public function get isCalloutVisible():Boolean {
            return callout.visible;
        }

        public function get calloutWidth():Number {
            return callout.width;
        }

        public function get calloutHeight():Number {
            return CALLOUT_HEIGHT;
        }

        public function hitTestUi(parentX:Number, parentY:Number):Boolean {
            var parentPoint:Point = new Point(parentX, parentY);
            var localPoint:Point = globalToLocal(
                parent.localToGlobal(parentPoint));
            var localX:Number = localPoint.x;
            var localY:Number = localPoint.y;
            if (localX * localX + localY * localY <= 100) {
                return true;
            }
            return callout.visible && callout.getBounds(this).contains(
                localX, localY);
        }

        public function layoutCallout(boxX:Number, boxY:Number,
                                      leader:Array):void {
            var localBox:Point = globalToLocal(
                parent.localToGlobal(new Point(boxX, boxY)));
            callout.x = localBox.x;
            callout.y = localBox.y;
            callout.alpha = 1;

            connector.graphics.clear();
            if (leader == null || leader.length < 2) {
                return;
            }
            connector.graphics.lineStyle(1, 0xE6DFAE, 1);
            var first:Array = leader[0] as Array;
            var localPoint:Point = overlayToLocal(first);
            connector.graphics.moveTo(localPoint.x, localPoint.y);
            for (var index:int = 1; index < leader.length; index++) {
                localPoint = overlayToLocal(leader[index] as Array);
                connector.graphics.lineTo(localPoint.x, localPoint.y);
            }
        }

        private function overlayToLocal(value:Array):Point {
            return globalToLocal(parent.localToGlobal(new Point(
                Number(value[0]), Number(value[1]))));
        }

        public function dispose():void {
            pointId = null;
            currentLabel = null;
            labelField = null;
            calloutBackground = null;
            callout = null;
            connector = null;
            ring = null;
            dot = null;
        }

        private function setLabel(value:String):void {
            if (currentLabel == value) {
                return;
            }
            currentLabel = value;
            labelField.text = value;
            calloutBackground.graphics.clear();
            calloutBackground.graphics.lineStyle(1, 0xD8CF96, 0.72);
            calloutBackground.graphics.beginFill(0x11151B, 0.88);
            calloutBackground.graphics.drawRoundRect(
                0, 0, labelField.width + CALLOUT_PADDING * 2,
                CALLOUT_HEIGHT, 6, 6);
            calloutBackground.graphics.endFill();
        }

        private function updateCalloutVisibility():void {
            callout.visible = calloutsEnabled && (persistentCallout || hovered);
            connector.visible = callout.visible;
        }
    }
}
