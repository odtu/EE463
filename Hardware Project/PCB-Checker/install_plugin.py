#!/usr/bin/env python3
"""Install the EE463 PCB Check button into KiCad (8, 9 or 10).

    python install_plugin.py            install for every KiCad version found
    python install_plugin.py --remove   uninstall

Then in the KiCad PCB editor: Tools > External Plugins > Refresh Plugins.
"""

import glob
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "ee463_pcb_check"


def documents_dir():
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                return os.path.expandvars(winreg.QueryValueEx(k, "Personal")[0])
        except OSError:
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def plugin_dirs():
    """scripting/plugins folders of the KiCad versions on this computer."""
    bases = []
    if sys.platform.startswith("linux"):
        bases.append(os.path.join(os.path.expanduser("~"), ".local", "share", "kicad"))
    bases.append(os.path.join(documents_dir(), "KiCad"))
    found = []
    for base in bases:
        for vdir in sorted(glob.glob(os.path.join(base, "[0-9]*.[0-9]*"))):
            try:
                if float(os.path.basename(vdir)) >= 8.0:
                    found.append(os.path.join(vdir, "scripting", "plugins"))
            except ValueError:
                pass
    if not found:  # KiCad never started yet: guess from the installed program
        for prog in glob.glob(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "KiCad", "*")):
            found.append(os.path.join(bases[-1], os.path.basename(prog), "scripting", "plugins"))
    return found


def main():
    remove = "--remove" in sys.argv
    dirs = plugin_dirs()
    if not dirs:
        print("No KiCad 8/9/10 found. Install KiCad and open it once, then run this again.")
        return 1
    for d in dirs:
        target = os.path.join(d, NAME)
        if os.path.isdir(target):
            shutil.rmtree(target)
        if remove:
            print(f"Removed {target}")
            continue
        os.makedirs(target, exist_ok=True)
        for f in ("__init__.py", "icon.png", "README.md"):
            shutil.copy2(os.path.join(HERE, "kicad_plugin", f), target)
        shutil.copytree(os.path.join(HERE, "pcbcheck"), os.path.join(target, "pcbcheck"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"Installed into {target}")
    if not remove:
        print("\nOpen the PCB editor and choose Tools > External Plugins > Refresh Plugins.\n"
              "The 'EE463 PCB Check' button appears in the top toolbar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
