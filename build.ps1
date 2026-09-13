param(
    [string]$Version = '0.1.1',
    [string]$Python = 'C:\Python27\python.exe'
)
$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Use a version such as 0.1.0' }
$buildRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.build'))
if ($buildRoot -ne (Join-Path $PSScriptRoot '.build')) { throw 'Invalid staging path' }
if (Test-Path -LiteralPath $buildRoot) { Remove-Item -LiteralPath $buildRoot -Recurse -Force }
New-Item -ItemType Directory -Path $buildRoot, (Join-Path $PSScriptRoot 'dist') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'res') -Destination $buildRoot -Recurse
& $Python -B (Join-Path $PSScriptRoot 'tools/package.py') $Version
if ($LASTEXITCODE -ne 0) { throw 'Compilation or packaging failed' }
