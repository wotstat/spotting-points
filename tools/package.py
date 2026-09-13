"""Compile only staged sources and package both client extensions."""
import os
import py_compile
import sys
import zipfile

if sys.version_info[:2] != (2, 7):
    raise RuntimeError('Build requires Python 2.7')

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
staging = os.path.join(root, '.build')
version = sys.argv[1]
entry = os.path.join(staging, 'res', 'scripts', 'client', 'gui', 'mods',
                     'mod_wotstat_spotting_points.py')
with open(entry, 'rb') as source:
    data = source.read()
with open(entry, 'wb') as source:
    source.write(data.replace('{{VERSION}}', version))
meta = ('<root><id>wotstat.spotting-points</id><version>{0}</version>'
        '<name>WotStat Spotting Points</name><description>Hangar visibility and '
        'observation points</description></root>').format(version)
with open(os.path.join(staging, 'meta.xml'), 'wb') as output:
    output.write(meta)
runtimeFiles = ['meta.xml']
for directory, _, names in os.walk(os.path.join(staging, 'res')):
    for name in sorted(names):
        path = os.path.join(directory, name)
        relative = os.path.relpath(path, staging).replace('\\', '/')
        if name.endswith('.py'):
            py_compile.compile(path, cfile=path + 'c', dfile=relative, doraise=True)
            runtimeFiles.append(relative + 'c')
        else:
            runtimeFiles.append(relative)
for extension in ('mtmod', 'wotmod'):
    artifact = os.path.join(root, 'dist', 'wotstat.spotting-points_{0}.{1}'.format(version, extension))
    with zipfile.ZipFile(artifact, 'w', zipfile.ZIP_STORED) as package:
        for relative in sorted(runtimeFiles):
            package.write(os.path.join(staging, relative), relative)
    print(artifact)
