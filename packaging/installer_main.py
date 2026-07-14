"""AlMunqith per-user installer (frozen to AlMunqith-Setup.exe).

Installs to %LOCALAPPDATA%\\Programs\\AlMunqith (no administrator needed),
creates Start-Menu and Desktop shortcuts, registers an uninstall entry, and
drops an uninstaller. A tiny PySide6 window shows progress in Arabic/English
so the user never sees a terminal.

The application payload (the onedir build) is bundled next to this script via
PyInstaller --add-data as the "payload" folder.
"""
import os
import sys
import shutil
import subprocess
import winreg

APP_NAME = "AlMunqith"
DISPLAY_NAME = "المنقذ - AlMunqith"
PUBLISHER = "AlMunqith"
VERSION = "0.2.0"


def _base_dir() -> str:
    # when frozen, payload sits in the PyInstaller temp dir (_MEIPASS)
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def install_dir() -> str:
    root = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(root, "Programs", APP_NAME)


def _make_shortcut(link_path: str, target: str, icon: str, desc: str):
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{link}');"
        "$s.TargetPath='{target}';"
        "$s.IconLocation='{icon}';"
        "$s.Description='{desc}';"
        "$s.WorkingDirectory='{wd}';"
        "$s.Save()"
    ).format(link=link_path, target=target, icon=icon, desc=desc,
             wd=os.path.dirname(target))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True)


def _register_uninstall(app_exe: str, uninstaller: str, icon: str):
    key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, DISPLAY_NAME)
        winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
        winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, icon)
        winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                          f'"{uninstaller}"')
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ,
                          os.path.dirname(app_exe))
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)


def do_install(progress=lambda pct, msg: None) -> str:
    dest = install_dir()
    payload = os.path.join(_base_dir(), "payload")
    progress(5, "prepare")
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest, exist_ok=True)

    files = []
    for root, _dirs, names in os.walk(payload):
        for n in names:
            files.append(os.path.join(root, n))
    total = max(1, len(files))
    for i, src in enumerate(files):
        rel = os.path.relpath(src, payload)
        tgt = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        shutil.copy2(src, tgt)
        progress(5 + int(80 * (i + 1) / total), "copy")

    app_exe = os.path.join(dest, f"{APP_NAME}.exe")
    icon = app_exe
    progress(88, "shortcuts")

    start_menu = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs", f"{APP_NAME}.lnk")
    os.makedirs(os.path.dirname(start_menu), exist_ok=True)
    _make_shortcut(start_menu, app_exe, icon, DISPLAY_NAME)

    desktop = os.path.join(os.path.expanduser("~"), "Desktop", f"{APP_NAME}.lnk")
    _make_shortcut(desktop, app_exe, icon, DISPLAY_NAME)

    progress(94, "register")
    uninstaller = os.path.join(dest, "uninstall.exe")
    # the same frozen exe acts as uninstaller when passed --uninstall
    shutil.copy2(sys.executable, uninstaller)
    _register_uninstall(app_exe, uninstaller + " --uninstall", icon)

    progress(100, "done")
    return app_exe


def do_uninstall(progress=lambda pct, msg: None):
    dest = install_dir()
    progress(20, "shortcuts")
    for lnk in (
        os.path.join(os.environ.get("APPDATA", ""),
                     r"Microsoft\Windows\Start Menu\Programs", f"{APP_NAME}.lnk"),
        os.path.join(os.path.expanduser("~"), "Desktop", f"{APP_NAME}.lnk"),
    ):
        try:
            os.remove(lnk)
        except OSError:
            pass
    progress(50, "registry")
    try:
        winreg.DeleteKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}")
    except OSError:
        pass
    progress(70, "files")
    # schedule self-deleting removal of the install dir
    bat = os.path.join(os.environ.get("TEMP", dest), "almunqith_uninst.bat")
    with open(bat, "w", encoding="utf-8") as f:
        f.write("@echo off\r\n:retry\r\n"
                f'rmdir /s /q "{dest}"\r\n'
                f'if exist "{dest}" (ping 127.0.0.1 -n 2 >nul & goto retry)\r\n'
                f'del "%~f0"\r\n')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)
    progress(100, "done")


if __name__ == "__main__":
    from almunqith_setup_ui import run_gui  # bundled sibling module
    run_gui(sys.argv)
