# Локальные библиотеки Scaleform

В эту папку извлекаются SWC целевого клиента: `base_app`, `battle`,
`common`, `common_i18n_library`, `gui_base`, `gui_battle`, `gui_lobby` и
`lobby`. Файлы нужны только компилятору как external libraries:
они не встраиваются в SWF, не попадают в пакет мода и игнорируются Git.

Для runtime-проверки «Мира танков» используйте библиотеки из
`res/packages/gui-part1.pkg` и `res/packages/gui-part2.pkg` установленного
клиента. `playerglobal.swc` берётся из Apache Royale отдельно. Для
проверки WoT пересоберите окно с библиотеками соответствующего клиента.
