# PyInstaller spec: AlMunqith-Setup.exe (per-user installer)
# Prereq: the onedir app build must already exist at dist\AlMunqith\
# Build:  .venv\Scripts\python.exe -m PyInstaller packaging\installer.spec --noconfirm
import os

ROOT = os.path.abspath(os.getcwd())
PAYLOAD = os.path.join(ROOT, "dist", "AlMunqith")   # onedir app build

# bundle the entire app build under "payload/" inside the setup exe
datas = []
for root, _dirs, files in os.walk(PAYLOAD):
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(root, PAYLOAD)
        dest = os.path.join("payload", rel) if rel != "." else "payload"
        datas.append((full, dest))

a = Analysis(
    [os.path.join(ROOT, "packaging", "installer_main.py")],
    pathex=[os.path.join(ROOT, "packaging")],
    binaries=[],
    datas=datas,
    hiddenimports=["almunqith_setup_ui"],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AlMunqith-Setup",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(ROOT, "packaging", "almunqith.ico"),
    uac_admin=False,           # per-user install: no admin needed
)
