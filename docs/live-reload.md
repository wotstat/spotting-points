# Обновление мода без перезапуска игры

Проверено в живом клиенте «Мир танков» 1.45.0.0 через WotStat REPL MCP 1.4.1.
Это рабочая инструкция для следующих агентов, а не универсальный reload любых
модов. Обновляем только собственные модули, окна и ресурсы Spotting Points.

## Окружение и короткий цикл

- Репозиторий: `E:/wot-mods/wotstat-spot-points`.
- Проверенный клиент: `E:/Games/Tanki`. Перед работой вызови `wot_list_clients`
  и проверь путь, версию, готовность агента и capabilities.
- Код выполняется инструментом `wot_exec` внутри Python 2.7 клиента, на главном
  потоке. Используй короткие вызовы; не запускай там сборку, ожидания и большие
  обходы файлов. Сборка выполняется внешним PowerShell.
- Исходники API: `E:/wot-mods/wot-src-ru`, ветка `mt-ru`. Для изменений игровых
  контрактов используй навык `wot-mod-development` и соответствующие исходники.

Обычный цикл: правка → подходящие тесты и сборка → применение через REPL →
проверка состояния и изображения в игре → сохранение изменений в Git.

```powershell
./build.ps1 -Version 0.3.18 -Python C:/Python27/python.exe
C:/Python27/python.exe -B -m unittest discover -s tests
```

Версию выбирай по текущей итерации. Дождись успешного завершения команды:
если инструмент вернул session ID, сборка ещё не закончилась. Результаты:
`.build/res/gui/flash/*.swf` и `dist/*.mtmod`, `dist/*.wotmod`.

## Python: небольшая адресная правка

В проверенной сессии модули загружены как
`gui.mods.wotstat_spotting_points.*`. Не импортируй одновременно вторую копию
под именем `wotstat_spotting_points.*`: это даст независимые globals и классы.
Если имя отличается, найди уже загруженный модуль в `sys.modules` и используй
его пространство имён. Старые переменные REPL могут указывать на уничтоженный
view; каждый раз бери актуальный `marker_view._view`.

Для самостоятельного алгоритма можно создать новую версию модуля и заменить
экземпляр, не трогая весь мод. Пример для `side_layout.py`:

```python
import sys, types
from gui.mods.wotstat_spotting_points import marker_view

sourceRoot = 'E:/wot-mods/wotstat-spot-points/res/scripts/client/gui/mods/wotstat_spotting_points/'
moduleName = 'gui.mods.wotstat_spotting_points.side_layout'
replacement = types.ModuleType(moduleName)
replacement.__package__ = 'gui.mods.wotstat_spotting_points'
replacement.__file__ = sourceRoot + 'side_layout.py'
exec compile(open(replacement.__file__, 'rb').read(), replacement.__file__, 'exec') in replacement.__dict__
sys.modules[moduleName] = replacement
setattr(sys.modules[replacement.__package__], 'side_layout', replacement)
marker_view.SideLayoutSolver = replacement.SideLayoutSolver

view = marker_view._view
# Применяй только если сейчас выбран SideLayoutSolver, а не другой вариант.
if view is not None and type(view._layoutSolver).__name__ == 'SideLayoutSolver':
    previous = view._layoutSolver
    solver = replacement.SideLayoutSolver()
    solver._revision = previous._revision
    solver._lastResult = previous._lastResult
    view._layoutSolver = solver
```

Перенос `_lastResult` уместен только при совместимом формате состояния. Иначе
создай чистый solver. Не переноси старую сигнатуру кэша: новая реализация должна
выполнить расчёт. Визуальные переходы хранятся отдельно в `_layoutTransitions`.

Важные ограничения Python reload:

- `from module import function` сохраняет ссылку. После замены функции нужно
  обновить её у потребителя, например
  `renderer.buildHighlightGroups = geometry.buildHighlightGroups`.
- Старые экземпляры остаются экземплярами старого класса. Пересоздай их или
  адресно обнови методы. Обновляй также ссылки для будущих экземпляров.
- DAAPI может хранить уже привязанный callback. Простое присваивание нового
  метода классу не всегда обновляет callback. Для совместимой правки мы меняли
  `oldMethod.im_func.func_code = newMethod.im_func.func_code`: объект функции
  остаётся прежним. Его globals при этом остаются старыми! Такой способ годится
  только при совместимых аргументах и closures, с обновлением нужных globals.
  При изменении интерфейса надёжнее пересоздать view.
- `exec` в существующем словаре модуля не удаляет исчезнувшие из исходника имена.
  Не полагайся на него для удаления устаревших hooks или состояния.

## Python: пересоздать мод целиком

Для изменений options/controller/view используй существующий lifecycle:
`bootstrap.fini()` снимает регистрации, callbacks и подписки, затем
`bootstrap.init(version)` создаёт мод заново. Не вызывай повторный `init` поверх
работающего мода и не обнуляй globals до cleanup.

Пример для текущей структуры (исполняется в REPL):

```python
import importlib
from gui.mods.wotstat_spotting_points import bootstrap

savedOptions = bootstrap.controller.getOptions()
bootstrap.fini()
prefix = 'gui.mods.wotstat_spotting_points'
sourceRoot = 'E:/wot-mods/wotstat-spot-points/res/scripts/client/gui/mods/wotstat_spotting_points/'

# Перечень зависит от правки; зависимости загружаются раньше потребителей.
for name in ('geometry', 'options', 'layout_solver', 'side_layout',
             'callout_transition', 'marker_logic', 'renderer',
             'marker_view', 'settings_view', 'controller', 'bootstrap'):
    module = importlib.import_module(prefix + '.' + name)
    path = sourceRoot + name + '.py'
    exec compile(open(path, 'rb').read(), path, 'exec') in module.__dict__

from gui.mods.wotstat_spotting_points import marker_view, settings_view
# Если менялся SWF, здесь задай VIEW_SWF для готовых preview-файлов,
# до bootstrap.init(), который регистрирует эти view.
bootstrap.init('live-preview')
for name, value in savedOptions.items():
    bootstrap.controller.setOption(name, value)
```

Добавь в порядок другие изменённые зависимости при необходимости. При смене
семантики настройки преобразуй сохранённое значение: например, при перестановке
вариантов А/Б использовалось `{0: 0, 1: 2, 2: 1}` для `calloutMode`, чтобы оставить
на экране тот же алгоритм. Не включай выключенные пользователем функции ради
reload; тестовые изменения настроек восстанавливай отдельно.

## AS3/SWF: обход кэша без перезапуска

Перезапись SWF под прежним именем недостаточна. Scaleform кэширует и ресурс,
и определения AS3-классов: даже новый файл может использовать старый класс.

1. Выполни обычную сборку для пакета.
2. Создай отдельную копию AS3 в `.local/preview<номер>/wotstat/spottingpoints/`.
3. В копии переименуй изменённые классы **и ссылки на них**:
   `SettingsWindow` → `SettingsWindowPreview17`, либо `MarkerOverlay` и
   `SpotPointMarker` → соответствующие имена с новым суффиксом. Имя файла должно
   совпадать с именем публичного класса. Не меняй этим способом основной исходник.
4. Скомпилируй preview теми же параметрами Royale, что использует `build.ps1`,
   но с source-path на preview-копию и новым именем выходного SWF.
5. Дождись завершения компиляции, затем загрузи новый view.

Параметры компилятора смотри в `build.ps1`: SWF target, player 17,
`as3/libs` и `playerglobal.swc` как external-library-path, корректный `JAVA_HOME`.
Для маркеров скопируй и переименуй вместе со ссылками также
`LayoutDebugOverlay.as` и `HoverGeometryOverlay.as`, от которых зависит overlay.

В этом клиенте `res_mods/1.45.0.0` имеет `cacheSubdirs="true"`: новые файлы,
добавленные после запуска в ранее отсутствовавшую папку, не обнаруживались.
`ResMgr.purge('gui/flash', True)` проблему не решал. Проверенный путь для preview:

```text
E:/Games/Tanki/res/gui/flash/wotstatMarkerOverlayPreview17.swf
```

Это добавление уникального ресурса нашего мода, а не замена штатного файла.
Не перезаписывай существующие игровые ресурсы. В проверенном клиенте `./res`
не имеет такого кэширования каталогов. Перед загрузкой проверь:

```python
import ResMgr
assert ResMgr.isFile('gui/flash/wotstatMarkerOverlayPreview17.swf')
```

Пересоздание только слоя маркеров:

```python
from gui.mods.wotstat_spotting_points import marker_view, bootstrap
marker_view.unregisterMarkerView()
marker_view.VIEW_SWF = 'wotstatMarkerOverlayPreview17.swf'
marker_view.registerMarkerView()
if bootstrap.controller.options.showUiPoints:
    marker_view.showMarkerView(bootstrap.controller)
```

Для настроек аналогично: `settings_view.unregisterSettingsView()`, новый
`VIEW_SWF`, `registerSettingsView()`, затем `showSettings(bootstrap.controller)`.
Загрузка асинхронная: `_view`/`_window` появляются на следующих кадрах. Не проверяй
успех только по отсутствию исключения у `showSettings`/`showMarkerView`.

## Проверка результата

- Для визуальной правки сделай `wot_screenshot` и проверь изображение.
- Проверь актуальный view, его `getState()` (2 — создан), нужный класс solver,
  `_layoutSolverFailed`, число маркеров и изменённые свойства.
- Интерактивные изменения проверь мышью через `wot_mouse`, затем прочитай
  фактическую опцию в `bootstrap.controller.options`. Координаты передавай
  в исходном разрешении игрового окна, а не уменьшенной картинки инструмента.
- Пример проверки импульсов: у существующего маркера вызови
  `updatePulse(0)`, `updatePulse(1750)`, `updatePulse(2000)`, `updatePulse(2600)`.
  У дочернего ring (`getChildAt(1)`) проверь visible/rotation/scaleX. Следующий
  игровой кадр восстановит актуальную общую фазу. Не создавай лишние тестовые
  маркеры без удаления и не разрывай связь native marker с Flash-объектом.
- Объекты PyGFx могут давать сохранённые значения свойств; при повторной проверке
  заново получай дочерний объект. Временный объект от `getTextFormat()` может
  оказаться недействительным в Python: для проверки стиля удобно читать `htmlText`.
- Проверь небольшой свежий хвост `E:/Games/Tanki/python.log` на ошибки после
  своего marker-времени. Не читай весь лог через REPL.

## Найденные особенности штатного UI

- Выпадающий список создаётся через linkage **`DropdownMenuUI`**, не
  `DropdownMenu`. Ему нужны `dropdown = "DropdownMenu_ScrollingList"` и
  `itemRenderer = "DropDownListItemRendererSound"`. Иначе кнопка может рисоваться,
  но список не открываться.
- Группы настроек используют `FieldSet`. Проверенный формат его заголовка:
  `$FieldFont`, 12 px, `#969687`, leading 2, kerning false, embedded fonts,
  advanced anti-aliasing. `getTextFormat()` на пустом поле давал Times New Roman
  чёрного цвета; заполни поле перед исследованием или используй проверенные
  параметры. Не выдавай дефолт пустого TextField за стиль клиента.

## Восстановление после ошибки preview

Сначала прочитай конкретную ошибку. При не найденном SWF исправь путь и проверь
`ResMgr.isFile`; если view не создан, сброс `_loading = False` соответствующего
модуля позволит повторить загрузку. Не сбрасывай его при нормальной загрузке.

При исключении в `_populate` наш SettingsWindow однажды оставался в состоянии
CREATING (1), а `destroy()` только откладывал уничтожение. После проверки
`DisposableEntity.py` в исходниках клиента применяли **только к этому сломанному
экземпляру нашего окна**:

```python
broken = settings_view._getApp().containerManager.getViewByKey(
    settings_view.ViewKey(settings_view.VIEW_ALIAS))
if broken is not None and broken.getState() == 1:
    # Только после подтверждённого исключения _populate, не во время загрузки.
    broken._DisposableEntity__lcState = 2
    broken.destroy()
```

Это аварийный приём для подтверждённого застрявшего preview, не обычный lifecycle.
Для штатного окна достаточно `destroy()`/`unregisterSettingsView()`.

## Что остаётся после проверки

Правки через REPL действуют в текущем процессе. Тестовые SWF сами по себе не
подменяют установленный пакет: после перезапуска загружается установленная версия.
Пакет ставится отдельно при закрытой игре с удалением только старого пакета этого
мода. Не оставляй две версии пакета одновременно.

Сохраняй исходники и документацию в Git; `.local/`, `.build/`, `dist/` игнорируются.
Удаляй только известные устаревшие preview-файлы, не каталог `res/gui/flash`.
Текущие preview-файлы оставь доступными, пока регистрации ссылаются на них: окно
или overlay могут пересоздаться позже в этой же сессии.
