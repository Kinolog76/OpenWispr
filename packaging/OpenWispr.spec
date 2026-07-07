# PyInstaller spec for OpenWispr.
# Run from the repo root:  pyinstaller --noconfirm --clean packaging/OpenWispr.spec
# Produces a windowed (no-console) app in dist\OpenWispr\OpenWispr.exe

import os

from PyInstaller.utils.hooks import collect_all

# Paths in a spec resolve relative to the spec's directory, so anchor
# everything to the repo root explicitly.
ROOT = os.path.dirname(SPECPATH)

datas, binaries, hiddenimports = [], [], []

# Packages that ship binary extensions / data files PyInstaller can miss.
for pkg in (
    "ctranslate2",
    "av",
    "onnxruntime",
    "faster_whisper",
    "sounddevice",
    "pystray",
    "pynput",
    "tokenizers",
    "huggingface_hub",
):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [os.path.join(ROOT, "openwispr", "__main__.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OpenWispr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(ROOT, "app.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OpenWispr",
)
