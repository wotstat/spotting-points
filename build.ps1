param(
    [string]$Version = '0.3.19',
    [string]$Python = 'C:\Python27\python.exe',
    [string]$Royale = "$env:LOCALAPPDATA\Programs\ApacheRoyale\0.9.12\royale-asjs",
    [string]$JavaHome = ''
)
$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Use a version such as 0.1.0' }
$compiler = Join-Path $Royale 'bin\mxmlc.bat'
$playerGlobal = Join-Path $Royale 'frameworks\libs\player\17.0\playerglobal.swc'
if (-not (Test-Path -LiteralPath $compiler)) { throw "Royale compiler not found: $compiler" }
if (-not (Test-Path -LiteralPath $playerGlobal)) { throw "playerglobal.swc not found: $playerGlobal" }
if ([string]::IsNullOrWhiteSpace($JavaHome)) {
    $javaCommand = Get-Command java.exe -ErrorAction Stop
    $JavaHome = Split-Path -Parent (Split-Path -Parent $javaCommand.Source)
}
if (-not (Test-Path -LiteralPath (Join-Path $JavaHome 'bin\java.exe'))) {
    throw "Java runtime not found below: $JavaHome"
}
$as3Libs = Join-Path $PSScriptRoot 'as3\libs'
$requiredSwcs = @(
    'base_app-1.0-SNAPSHOT.swc',
    'battle.swc',
    'common-1.0-SNAPSHOT.swc',
    'common_i18n_library-1.0-SNAPSHOT.swc',
    'gui_base-1.0-SNAPSHOT.swc',
    'gui_battle-1.0-SNAPSHOT.swc',
    'gui_lobby-1.0-SNAPSHOT.swc',
    'lobby.swc'
)
foreach ($swc in $requiredSwcs) {
    $swcPath = Join-Path $as3Libs $swc
    if (-not (Test-Path -LiteralPath $swcPath)) { throw "Client SWC not found: $swcPath" }
}
$buildRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.build'))
if ($buildRoot -ne (Join-Path $PSScriptRoot '.build')) { throw 'Invalid staging path' }
if (Test-Path -LiteralPath $buildRoot) { Remove-Item -LiteralPath $buildRoot -Recurse -Force }
New-Item -ItemType Directory -Path $buildRoot, (Join-Path $PSScriptRoot 'dist') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'res') -Destination $buildRoot -Recurse
$flashOutput = Join-Path $buildRoot 'res\gui\flash'
New-Item -ItemType Directory -Path $flashOutput -Force | Out-Null
$previousJavaHome = $env:JAVA_HOME
try {
    $env:JAVA_HOME = $JavaHome
    $flashTargets = @(
        @('wotstatSpottingPointsSettings.swf', 'SettingsWindow.as'),
        @('wotstatSpottingPointsMarkers.swf', 'MarkerOverlay.as')
    )
    foreach ($target in $flashTargets) {
        $outputPath = Join-Path $flashOutput $target[0]
        $sourcePath = Join-Path $PSScriptRoot "as3\src\wotstat\spottingpoints\$($target[1])"
        & $compiler '-compiler.targets=SWF' '-target-player=17.0' '-swf-version=17' '-debug=false' "-compiler.source-path=$PSScriptRoot\as3\src" "-compiler.external-library-path=$as3Libs,$playerGlobal" "-output=$outputPath" "$sourcePath"
        if ($LASTEXITCODE -ne 0) { throw "Scaleform compilation failed: $($target[1])" }
    }
}
finally {
    $env:JAVA_HOME = $previousJavaHome
}
& $Python -B (Join-Path $PSScriptRoot 'tools/package.py') $Version
if ($LASTEXITCODE -ne 0) { throw 'Compilation or packaging failed' }
