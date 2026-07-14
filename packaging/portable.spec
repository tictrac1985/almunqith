# PyInstaller spec: portable single-file AlMunqith.exe
# Build:  .venv\Scripts\python.exe -m PyInstaller packaging\portable.spec --noconfirm
import os
from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(ROOT, "almunqith", "ui", "strings_ar.json"), "almunqith/ui"),
    (os.path.join(ROOT, "almunqith", "ui", "strings_en.json"), "almunqith/ui"),
]

hiddenimports = collect_submodules("almunqith")

a = Analysis(
    [os.path.join(ROOT, "almunqith", "__main__.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=["tkinter", "pytest", "PySide6.QtWebEngineCore",
              "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
              "PySide6.QtCharts", "PySide6.QtDataVisualization",
              "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AlMunqith",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,               # windowed app, no terminal
    disable_windowed_traceback=False,
    icon=os.path.join(ROOT, "packaging", "almunqith.ico"),
    uac_admin=False,             # app self-elevates at runtime (see ui/elevate)
    version_file=None,
)
