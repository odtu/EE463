"""KiCad PCB editor plugin: one toolbar button that checks the open board and
opens the report in the browser. Installed by install_plugin.py."""

import os
import shutil
import sys
import tempfile
import traceback
import webbrowser

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _save_copy(board, folder):
    """Save the board as it is now (unsaved edits included) into folder, with its project files."""
    src = board.GetFileName()
    dst = os.path.join(folder, os.path.basename(src))
    try:
        pcbnew.SaveBoard(dst, board, True)  # True: do not touch the project settings
    except TypeError:
        pcbnew.SaveBoard(dst, board)
    if board.GetFileName() != src:  # never let the open board point at the temp copy
        board.SetFileName(src)
    proj_dir = os.path.dirname(src)
    stem = os.path.splitext(os.path.basename(src))[0]
    for name in os.listdir(proj_dir):
        if name.startswith(stem) and name.endswith((".kicad_pro", ".kicad_dru")) or name.endswith(".kicad_sch"):
            try:
                shutil.copy2(os.path.join(proj_dir, name), folder)
            except OSError:
                pass
    cfg = os.path.join(proj_dir, "pcb_checker.json")
    if os.path.exists(cfg):
        shutil.copy2(cfg, folder)
    return dst


class EE463PcbCheck(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "EE463 PCB Check"
        self.category = "Design checks"
        self.description = ("Checks the board against PCBWay's standard limits and the EE463 converter rules, "
                            "then opens a report in your browser. Works offline.")
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(HERE, "icon.png")
        self.dark_icon_file_name = os.path.join(HERE, "icon.png")

    def Run(self):
        import wx
        board = pcbnew.GetBoard()
        path = board.GetFileName()
        if not path:
            wx.MessageBox("Save the board first (File > Save), then run the check again.", "EE463 PCB Check")
            return
        try:
            filler = pcbnew.ZONE_FILLER(board)
            filler.Fill(board.Zones())
            pcbnew.Refresh()
        except Exception:
            pass
        tmp = tempfile.mkdtemp(prefix="ee463check_")
        busy = wx.BusyInfo("Checking the board... (KiCad's DRC can take up to a minute)")
        try:
            from pcbcheck import cli
            copy = _save_copy(board, tmp)
            out = os.path.splitext(path)[0] + "_check.html"
            report = cli.run(copy, out=out, quiet=True,
                             display_name=os.path.splitext(os.path.basename(path))[0], board_override=copy)
        except Exception:
            del busy
            wx.MessageBox("The checker crashed:\n\n" + traceback.format_exc()[-1500:], "EE463 PCB Check", wx.ICON_ERROR)
            return
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        del busy
        c = report.counts()
        webbrowser.open("file:///" + os.path.abspath(report.out).replace("\\", "/"))
        wx.MessageBox(f"{report.verdict()[1]}\n\n{c['error']} must fix, {c['warning']} should fix, {c['info']} to check.\n\n"
                      f"The report is open in your browser and saved as:\n{report.out}\n\n"
                      "Zones were refilled before the check.", "EE463 PCB Check")


EE463PcbCheck().register()
