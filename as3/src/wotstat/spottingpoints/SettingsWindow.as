package wotstat.spottingpoints {
    import net.wg.gui.components.controls.CheckBox;
    import net.wg.infrastructure.base.AbstractWindowView;
    import scaleform.clik.events.ButtonEvent;

    public class SettingsWindow extends AbstractWindowView {
        public var optionChanged:Function;

        private static const CONTENT_WIDTH:int = 420;
        private static const CONTENT_HEIGHT:int = 210;
        private static const LEFT:int = 24;
        private static const FIRST_ROW:int = 18;
        private static const ROW_HEIGHT:int = 36;
        private static const OPTION_NAMES:Array = [
            "showMaskPoints",
            "showSpotPoints",
            "showUiPoints",
            "showGuides",
            "allowTurretRotation"
        ];

        private var boxes:Object = {};

        public function SettingsWindow() {
            super();
            setSize(CONTENT_WIDTH, CONTENT_HEIGHT);
        }

        override protected function onPopulate():void {
            super.onPopulate();
            window.useBottomBtns = false;
            for (var index:int = 0; index < OPTION_NAMES.length; index++) {
                var optionName:String = OPTION_NAMES[index];
                var box:CheckBox = App.utils.classFactory.getComponent(
                    "CheckBox", CheckBox) as CheckBox;
                box.name = optionName;
                box.x = LEFT;
                box.y = FIRST_ROW + index * ROW_HEIGHT;
                box.width = CONTENT_WIDTH - LEFT * 2;
                box.addEventListener(ButtonEvent.CLICK, onOptionClick);
                addChild(box);
                boxes[optionName] = box;
            }
        }

        public function as_setData(options:Object, labels:Object):void {
            window.title = labels.title;
            for each (var optionName:String in OPTION_NAMES) {
                var box:CheckBox = boxes[optionName] as CheckBox;
                box.label = labels[optionName];
            }
            as_setOptions(options);
            visible = true;
        }

        public function as_setOptions(options:Object):void {
            for each (var optionName:String in OPTION_NAMES) {
                var box:CheckBox = boxes[optionName] as CheckBox;
                box.selected = Boolean(options[optionName]);
            }
        }

        private function onOptionClick(event:ButtonEvent):void {
            var box:CheckBox = event.currentTarget as CheckBox;
            optionChanged(box.name, box.selected);
        }

        override protected function onBeforeDispose():void {
            for each (var optionName:String in OPTION_NAMES) {
                var box:CheckBox = boxes[optionName] as CheckBox;
                box.removeEventListener(ButtonEvent.CLICK, onOptionClick);
            }
            super.onBeforeDispose();
        }

        override protected function onDispose():void {
            for each (var optionName:String in OPTION_NAMES) {
                var box:CheckBox = boxes[optionName] as CheckBox;
                box.dispose();
                boxes[optionName] = null;
            }
            boxes = null;
            optionChanged = null;
            super.onDispose();
        }
    }
}
