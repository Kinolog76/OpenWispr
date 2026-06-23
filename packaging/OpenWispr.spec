# PyInstaller spec for OpenWispr.
# Run from the repo root:  pyinstaller --noconfirm --clean packaging/OpenWispr.spec
# Produces a windowed (no-console) app in dist\OpenWispr\OpenWispr.exe

from PyInstaller.utils.hooks import collect_all

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
    ["openwispr/__main__.py"],
    pathex=["."],
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
    icon="app.ico",
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
