"""Command line: python check_pcb.py <board.kicad_pcb | project folder | submission.zip>"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
import webbrowser
import zipfile

from . import __version__
from .findings import Report
from .rules import PROJECT, FAB

SKIP_DIRS = re.compile(r"(-backups|_autosave|\.history|__MACOSX|\.git|node_modules)", re.I)


def _walk(folder):
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not SKIP_DIRS.search(d)]
        for f in files:
            if not f.startswith(("~", "_autosave", ".")):
                yield os.path.join(root, f)


def _safe_extract(zpath, dest):
    with zipfile.ZipFile(zpath) as z:
        for m in z.infolist():
            target = os.path.realpath(os.path.join(dest, m.filename))
            if not target.startswith(os.path.realpath(dest) + os.sep) and target != os.path.realpath(dest):
                continue  # skip entries that would land outside the folder
            if m.is_dir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(m) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    # nested zips (a Gerber zip inside the submission zip)
    for f in list(_walk(dest)):
        if f.lower().endswith(".zip"):
            sub = os.path.splitext(f)[0] + "_unzipped"
            os.makedirs(sub, exist_ok=True)
            try:
                _safe_extract(f, sub)
            except zipfile.BadZipFile:
                pass


def find_inputs(target):
    """Return (board_path or None, list of fab files, folder, all files, temp dir to delete)."""
    tmp = None
    if os.path.isfile(target) and target.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp(prefix="pcbcheck_zip_")
        _safe_extract(target, tmp)
        folder = tmp
    elif os.path.isfile(target):
        ext = os.path.splitext(target)[1].lower()
        if ext == ".kicad_pcb":
            return target, [], os.path.dirname(os.path.abspath(target)), [], None
        if ext == ".kicad_pro":
            pcb = os.path.splitext(target)[0] + ".kicad_pcb"
            return (pcb if os.path.exists(pcb) else None), [], os.path.dirname(os.path.abspath(target)), [], None
        folder = os.path.dirname(os.path.abspath(target))
    else:
        folder = target
    from .gerber import is_fab_file
    files = list(_walk(folder))
    pcbs = [f for f in files if f.lower().endswith(".kicad_pcb")]
    board = None
    if pcbs:
        pros = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".kicad_pro")}
        with_pro = [p for p in pcbs if os.path.splitext(p)[0] in pros]
        board = max(with_pro or pcbs, key=lambda p: (os.path.getsize(p), -p.count(os.sep)))
    fab = [f for f in files if is_fab_file(f) and not f.lower().endswith((".kicad_pcb", ".kicad_sch"))]
    if fab:
        by_dir = {}
        for f in fab:
            by_dir.setdefault(os.path.dirname(f), []).append(f)
        fab = max(by_dir.values(), key=len)
    return board, fab, folder, files, tmp


def load_config(*folders):
    for d in folders:
        if not d:
            continue
        p = os.path.join(d, "pcb_checker.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                cfg = json.load(fh)
            cfg["_path"] = p
            return cfg
    return {}


def check_submission(files, report, board, fab):
    report.check("SUB-FILES", "submission", "Submission contains all files", "EE463 step 8")
    low = [f.lower() for f in files]
    has_sch = any(f.endswith((".kicad_sch", ".schdoc", ".sch")) for f in low) or \
        any(f.endswith(".pdf") and "sch" in os.path.basename(f) for f in low)
    has_pcb = bool(board) or any(f.endswith((".pcbdoc", ".brd", ".kicad_pcb")) for f in low)
    has_bom = any(f.endswith((".csv", ".xlsx", ".xls", ".ods")) and ("bom" in os.path.basename(f) or "bill" in os.path.basename(f))
                  for f in low) or any(f.endswith((".csv", ".xlsx")) for f in low)
    if not fab:
        report.add("SUB-FILES", "error", "No Gerber/drill files found. The fab needs them (plot Gerbers + drill files and add them).")
    if not has_sch:
        report.add("SUB-FILES", "warning", "No schematic file found (.kicad_sch, or a PDF of the schematic).")
    if not has_pcb:
        report.add("SUB-FILES", "warning", "No PCB source file found (.kicad_pcb).")
    if not has_bom:
        report.add("SUB-FILES", "warning", "No bill of materials found (a .csv or .xlsx with 'bom' in its name).",
                   fix="KiCad schematic editor: Tools > Generate Bill of Materials, export as CSV.")


def run(target, out=None, overload=None, copper=None, drc=True, quiet=False, display_name=None, board_override=None):
    t0 = time.time()

    def say(*a):
        if not quiet:
            print(*a)

    if board_override:
        board_path, fab, folder, files, tmp = board_override, [], os.path.dirname(board_override), [], None
    else:
        board_path, fab, folder, files, tmp = find_inputs(target)
    cfg = load_config(os.path.dirname(board_path) if board_path else None, folder,
                      os.path.dirname(os.path.abspath(target)) if os.path.isfile(target) else target)
    if overload is None:
        overload = bool(cfg.get("overload", False))
    report = Report()
    report.source = os.path.abspath(target)
    report.board_name = display_name or (os.path.splitext(os.path.basename(board_path))[0] if board_path else os.path.basename(os.path.abspath(target)))
    rated = PROJECT["iout_overload"] if overload else PROJECT["iout_rated"]
    report.settings = {
        "Checker": f"pcbcheck {__version__}",
        "Project": f"{PROJECT['name']}: {PROJECT['vin_min']:g}-{PROJECT['vin_max']:g} V in, {PROJECT['vout']:g} V / {rated:g} A out"
                   + (" (overload bonus)" if overload else " (use --overload to check for 7.5 A)"),
        "Fab limits": FAB["name"] + " (track/space 0.15 mm, drill 0.3 mm, 2 layers, 1.6 mm, 1 oz)",
    }
    if cfg.get("_path"):
        report.settings["Config file"] = cfg["_path"]
    drawing = None
    if files and not board_override:
        check_submission(files, report, board_path, fab)

    if board_path:
        from .kicad_board import load_board
        from .checks_kicad import run_kicad_checks
        from . import drawing as dr
        say(f"Reading {board_path}")
        b = load_board(board_path)
        oz = copper or cfg.get("copper_oz")
        ctx = run_kicad_checks(b, report, cfg.get("nets"), overload, oz)
        report.detected = ctx.a.summary()
        bb = b.edge.bbox
        report.meta = {
            "Board size": f"{bb[2] - bb[0]:.1f} x {bb[3] - bb[1]:.1f} mm" if bb else "no outline",
            "Copper layers": str(len(b.copper_layers)),
            "Thickness": f"{b.thickness:g} mm" if b.thickness else "?",
            "Copper": f"{ctx.oz:g} oz",
            "Parts": str(len([f for f in b.footprints if f.ref and not f.ref.startswith('#')])),
            "Tracks / vias": f"{len(b.tracks)} / {len(b.vias)}",
            "Checked for": f"{rated:g} A out" + (" (overload)" if overload else ""),
            "KiCad file": b.generator_version or b.version,
        }
        if drc:
            from .drc import run_drc
            say("Running KiCad DRC (kicad-cli)...")
            run_drc(board_path, report)
        drawing = dr.from_kicad(b)
    if fab:
        from .gerber import load_fab_files
        from .checks_gerber import run_gerber_checks
        from . import drawing as dr
        say(f"Reading {len(fab)} Gerber/drill files in {os.path.dirname(fab[0])}")
        fs = load_fab_files(fab)
        run_gerber_checks(fs, report, copper or cfg.get("copper_oz") or 1.0)
        if drawing is None:
            drawing = dr.from_gerber(fs)
            bb = drawing["bbox"]
            report.meta = {
                "Board size": f"{bb[2] - bb[0]:.1f} x {bb[3] - bb[1]:.1f} mm",
                "Copper layers": str(len(fs.copper())),
                "Holes": str(sum(1 for _ in fs.all_holes())),
                "Files": str(len(fs.layers) + len(fs.drills)),
            }
            report.notes.append("Only Gerber/drill files were checked. The power-stage, layout and test-point checks need "
                                "KiCad files (.kicad_pcb). Groups using another EDA tool should check those by hand.")
    if not board_path and not fab:
        raise SystemExit(f"No KiCad board (.kicad_pcb) or Gerber files found in {target}")
    report.drawing = drawing
    report.apply_waivers(cfg.get("waivers"), cfg.get("ignore"))

    if out is None:
        base_dir = os.path.dirname(os.path.abspath(target)) if (tmp or os.path.isfile(target)) else os.path.abspath(target)
        if board_override:
            base_dir = os.path.dirname(os.path.abspath(target))
        out = os.path.join(base_dir, f"{report.board_name}_check.html")
    from .report_html import render
    render(report, out)
    with open(os.path.splitext(out)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=1)
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    report.out = out
    report.elapsed = time.time() - t0
    return report


def print_summary(report):
    c = report.counts()
    print()
    print(f"  {report.verdict()[1]}")
    print(f"  {c['error']} must fix, {c['warning']} should fix, {c['info']} to check")
    for f in report.findings():
        if f.severity in ("error", "warning"):
            tag = "MUST FIX  " if f.severity == "error" else "SHOULD FIX"
            print(f"  [{tag}] {f.title}: {f.message[:160]}")
    print(f"\n  Report: {report.out}  ({report.elapsed:.1f} s)")


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(prog="check_pcb",
                                description="EE463 PCB checker: PCBWay limits, power stage, layout and test points.")
    p.add_argument("target", help=".kicad_pcb file, project folder, or submission .zip (Gerbers + drill + sources)")
    p.add_argument("-o", "--out", help="report file (default: <board>_check.html next to the input)")
    p.add_argument("--overload", action="store_true", default=None, help="check for the 90 W / 7.5 A overload bonus")
    p.add_argument("--copper", type=float, help="outer copper weight in oz (default: from the stackup, else 1)")
    p.add_argument("--no-drc", action="store_true", help="skip KiCad's own DRC (kicad-cli)")
    p.add_argument("--open", action="store_true", help="open the report in the browser")
    a = p.parse_args(argv)
    if not os.path.exists(a.target):
        p.error(f"{a.target} does not exist")
    report = run(a.target, a.out, a.overload, a.copper, not a.no_drc)
    print_summary(report)
    if a.open:
        webbrowser.open("file:///" + os.path.abspath(report.out).replace("\\", "/"))
    return 1 if report.counts()["error"] else 0
