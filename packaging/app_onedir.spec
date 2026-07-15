# PyInstaller spec: onedir app build (payload for the installer)
# Build:  .venv\Scripts\python.exe -m PyInstaller packaging\app_onedir.spec --noconfirm
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
    excludes=["tkinter", "pytest", "PySide6.QtWebEngineCore",
              "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
              "PySide6.QtCharts", "PySide6.QtDataVisualization",
              "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia",
              "PySide6.QtNetwork", "PySide6.QtSql", "PySide6.QtQuick3D",
              "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtWebSockets",
              "PySide6.QtWebChannel", "PySide6.QtPositioning",
              "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtSensors",
              "PySide6.QtSerialPort", "PySide6.QtTest", "PySide6.QtOpenGL",
              "PySide6.QtQuickWidgets", "PySide6.QtRemoteObjects"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="AlMunqith",
    console=False,
    icon=os.path.join(ROOT, "packaging", "almunqith.ico"),
    uac_admin=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="AlMunqith")
