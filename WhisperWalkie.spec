# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('flet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('flet_desktop')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Bundle the app icon for Linux desktop shortcut support.
icon_png = os.path.join(os.getcwd(), 'assets', 'icon-512.png')
if os.path.isfile(icon_png):
    datas += [(icon_png, '.')]

# Bundle platform install scripts for easy onboarding.
for script in ['install-linux.sh', 'install-macos.sh']:
    script_path = os.path.join(os.getcwd(), script)
    if os.path.isfile(script_path):
        datas += [(script_path, '.')]

# Bundle the pre-downloaded Whisper base model so the app works offline.
# The model directory is expected at ./faster-whisper-base/ at build time
# (the CI workflow downloads it before running PyInstaller).
model_dir = os.path.join(os.getcwd(), 'faster-whisper-base')
if os.path.isdir(model_dir):
    datas += [(model_dir, 'faster-whisper-base')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhisperWalkie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhisperWalkie',
)
