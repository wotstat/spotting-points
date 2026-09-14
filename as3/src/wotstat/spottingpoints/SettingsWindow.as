package wotstat.spottingpoints {
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.text.AntiAliasType;
    import net.wg.gui.components.controls.CheckBox;
    import net.wg.gui.components.controls.DropdownMenu;
    import net.wg.infrastructure.base.AbstractWindowView;
    import scaleform.clik.data.DataProvider;
    import scaleform.clik.events.ButtonEvent;
    import scaleform.clik.events.ListEvent;

    public class SettingsWindow extends AbstractWindowView {
        public var optionChanged:Function;

        private static const CONTENT_WIDTH:int = 560;
        private static const CONTENT_HEIGHT:int = 212;
        private static const LEFT:int = 24;
        private static const RIGHT:int = 300;
        private static const ROW_HEIGHT:int = 34;
        private static const OPTION_NAMES:Array = [
            "showMaskPoints", "showSpotPoints", "showGuides",
            "showUiPoints", "allowTurretRotation", "layoutDebug"
        ];
        private var boxes:Object = {};
        private var headings:Object = {};
        private var calloutMode:DropdownMenu;
        private var selectedMode:int = 1;
        private var updating:Boolean = false;

        public function SettingsWindow() {
            super();
            setSize(CONTENT_WIDTH, CONTENT_HEIGHT);
        }

        override protected function onPopulate():void {
            super.onPopulate();
            window.useBottomBtns = false;
            createHeading("group3d", LEFT, 14);
            createHeading("groupUi", RIGHT, 14);
            createHeading("callouts", RIGHT, 81);
            for (var index:int = 0; index < OPTION_NAMES.length; index++) {
                var optionName:String = OPTION_NAMES[index];
                var box:CheckBox = App.utils.classFactory.getComponent(
                    "CheckBox", CheckBox) as CheckBox;
                box.name = optionName;
                box.x = index == 3 ? RIGHT : LEFT;
                box.y = index < 3 ? 48 + index * ROW_HEIGHT :
                    (index == 3 ? 48 : 166 + (index - 4) * ROW_HEIGHT);
                box.width = index < 4 ? 236 : CONTENT_WIDTH - LEFT * 2;
                box.addEventListener(ButtonEvent.CLICK, onOptionClick);
                box.visible = optionName != "layoutDebug";
                addChild(box);
                boxes[optionName] = box;
            }
            calloutMode = App.utils.classFactory.getComponent(
                "DropdownMenuUI", DropdownMenu) as DropdownMenu;
            calloutMode.x = RIGHT;
            calloutMode.name = "calloutMode";
            calloutMode.y = 105;
            calloutMode.width = 236;
            calloutMode.dropdown = "DropdownMenu_ScrollingList";
            calloutMode.itemRenderer = "DropDownListItemRendererSound";
            calloutMode.menuRowCount = 3;
            calloutMode.addEventListener(ListEvent.INDEX_CHANGE, onModeChange);
            addChild(calloutMode);
        }

        private function createHeading(key:String, xPos:int, yPos:int):void {
            var field:TextField = new TextField();
            // Same format as the client's settings FieldSet.textField.
            var format:TextFormat = new TextFormat("$FieldFont", 12, 0x969687);
            format.leading = 2;
            format.kerning = false;
            field.defaultTextFormat = format;
            field.embedFonts = true;
            field.antiAliasType = AntiAliasType.ADVANCED;
            field.x = xPos;
            field.y = yPos;
            field.width = 236;
            field.height = 28;
            field.mouseEnabled = false;
            field.selectable = false;
            addChild(field);
            headings[key] = field;
        }

        private function drawGroupFrame(left:int, heading:TextField):void {
            var right:int = left + 260;
            var top:int = 24;
            var bottom:int = 148;
            graphics.lineStyle(1, 0x77776B, 0.45);
            graphics.moveTo(heading.x - 4, top);
            graphics.lineTo(left, top);
            graphics.lineTo(left, bottom);
            graphics.lineTo(right, bottom);
            graphics.lineTo(right, top);
            graphics.lineTo(heading.x + heading.textWidth + 6, top);
        }

        public function as_setData(options:Object, labels:Object,
                                   showDebugOption:Boolean):void {
            window.title = labels.title;
            for each (var optionName:String in OPTION_NAMES) {
                boxes[optionName].label = labels[optionName];
            }
            for (var key:String in headings) {
                headings[key].text = labels[key];
            }
            graphics.clear();
            drawGroupFrame(LEFT - 12, headings.group3d as TextField);
            drawGroupFrame(RIGHT - 12, headings.groupUi as TextField);
            updating = true;
            calloutMode.dataProvider = new DataProvider(labels.calloutModes as Array);
            updating = false;
            boxes.layoutDebug.visible = showDebugOption;
            setSize(CONTENT_WIDTH, CONTENT_HEIGHT +
                (showDebugOption ? ROW_HEIGHT : 0));
            as_setOptions(options);
            visible = true;
        }

        public function as_setOptions(options:Object):void {
            updating = true;
            for each (var optionName:String in OPTION_NAMES) {
                boxes[optionName].selected = Boolean(options[optionName]);
            }
            selectedMode = int(options.calloutMode);
            calloutMode.selectedIndex = selectedMode;
            updating = false;
        }

        private function onOptionClick(event:ButtonEvent):void {
            var box:CheckBox = event.currentTarget as CheckBox;
            optionChanged(box.name, box.selected);
        }

        private function onModeChange(event:ListEvent):void {
            if (!updating && calloutMode.selectedIndex >= 0 &&
                    calloutMode.selectedIndex != selectedMode) {
                selectedMode = calloutMode.selectedIndex;
                optionChanged("calloutMode", selectedMode);
            }
        }

        override protected function onBeforeDispose():void {
            for each (var optionName:String in OPTION_NAMES) {
                boxes[optionName].removeEventListener(ButtonEvent.CLICK, onOptionClick);
            }
            calloutMode.removeEventListener(ListEvent.INDEX_CHANGE, onModeChange);
            super.onBeforeDispose();
        }

        override protected function onDispose():void {
            for each (var optionName:String in OPTION_NAMES) {
                boxes[optionName].dispose();
            }
            calloutMode.dispose();
            calloutMode = null;
            boxes = null;
            headings = null;
            optionChanged = null;
            super.onDispose();
        }
    }
}
