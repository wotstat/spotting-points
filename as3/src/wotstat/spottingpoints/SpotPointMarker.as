package wotstat.spottingpoints {
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.geom.Point;
    import flash.text.AntiAliasType;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;
    import scaleform.clik.motion.Tween;

    public class SpotPointMarker extends Sprite {
        private static const DOT_RADIUS:Number = 4;
        private static const CALLOUT_HEIGHT:Number = 24;
        private static const CALLOUT_PADDING:Number = 8;
        private static const PULSE_DURATION:Number = 850;
        private static const PULSE_DELAY:Number = 1750;

        public var pointId:String;

        private var dot:Shape;
        private var ring:Shape;
        private var connector:Shape;
        private var callout:Sprite;
        private var calloutBackground:Shape;
        private var labelField:TextField;
        private var pulseTween:Tween;
        private var persistentCallout:Boolean = false;
        private var hovered:Boolean = false;
        private var currentLabel:String = "";

        public function SpotPointMarker(id:String, label:String) {
            super();
            pointId = id;
            mouseEnabled = false;
            mouseChildren = false;

            connector = new Shape();
            addChild(connector);

            ring = new Shape();
            ring.graphics.lineStyle(1.5, 0xFFF2B2, 0.72);
            ring.graphics.drawCircle(0, 0, DOT_RADIUS + 2);
            ring.alpha = 0.72;
            addChild(ring);

            dot = new Shape();
            dot.graphics.lineStyle(2, 0xFFF5C9, 1);
            dot.graphics.beginFill(0x22252A, 0.96);
            dot.graphics.drawCircle(0, 0, DOT_RADIUS);
            dot.graphics.endFill();
            addChild(dot);

            callout = new Sprite();
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
            labelField.y = 3;
            callout.addChild(labelField);
            addChild(callout);
            setLabel(label);
            updateCalloutVisibility();

            pulseTween = new Tween(PULSE_DURATION, ring, {
                "alpha": 0,
                "scaleX": 2.6,
                "scaleY": 2.6
            }, {
                "delay": PULSE_DELAY,
                "loop": true
            });
        }

        public function setData(label:String, showCallout:Boolean):void {
            setLabel(label);
            persistentCallout = showCallout;
            updateCalloutVisibility();
        }

        public function setHovered(value:Boolean):void {
            hovered = value;
            updateCalloutVisibility();
        }

        public function get isCalloutVisible():Boolean {
            return callout.visible;
        }

        public function get calloutWidth():Number {
            return callout.width;
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

        public function layoutCallout(edgeX:Number, centerY:Number,
                                      placeLeft:Boolean):void {
            var parentPoint:Point = new Point(edgeX, centerY);
            var localPoint:Point = globalToLocal(
                parent.localToGlobal(parentPoint));
            var localX:Number = localPoint.x;
            var localY:Number = localPoint.y;
            callout.x = placeLeft ? localX - callout.width : localX;
            callout.y = localY - CALLOUT_HEIGHT * 0.5;
            connector.graphics.clear();
            connector.graphics.lineStyle(1, 0xE6DFAE, 0.78);
            connector.graphics.moveTo(0, 0);
            connector.graphics.lineTo(localX, localY);
        }

        public function dispose():void {
            if (pulseTween != null) {
                pulseTween.dispose();
                pulseTween = null;
            }
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
            callout.visible = persistentCallout || hovered;
            connector.visible = callout.visible;
        }
    }
}
