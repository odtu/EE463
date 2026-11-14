"""Run KiCad's own DRC through kicad-cli and add its results to the report."""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

_NOWIN = {"creationflags": 0x08000000} if os.name == "nt" else {}


def find_kicad_cli():
    names = ["kicad-cli.exe", "kicad-cli"] if os.name == "nt" else ["kicad-cli"]
    here = os.path.dirname(sys.executable)
    for n in names:
        p = os.path.join(here, n)
        if os.path.exists(p):
            return p
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    candidates = []
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", "")):
            if base:
                candidates += sorted(glob.glob(os.path.join(base, "KiCad", "*", "bin", "kicad-cli.exe")), reverse=True)
    elif sys.platform == "darwin":
        candidates += ["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"]
    else:
        candidates += ["/usr/bin/kicad-cli", "/usr/local/bin/kicad-cli"]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def kicad_version(cli):
    try:
        out = subprocess.run([cli, "version"], capture_output=True, text=True, timeout=30, **_NOWIN)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def run_drc(board_path, report, cli=None, timeout=600):
    cid = "DRC"
    report.check(cid, "drc", "KiCad design rules check (DRC)", "KiCad")
    report.check("DRC-UNROUTED", "drc", "Everything routed", "EST-008")
    report.check("DRC-PARITY", "drc", "Board matches the schematic", "KiCad")
    cli = cli or find_kicad_cli()
    if not cli:
        report.skip(cid, "kicad-cli not found (install KiCad 8 or newer, or run the checker with KiCad's Python)")
        report.skip("DRC-UNROUTED", "kicad-cli not found")
        report.skip("DRC-PARITY", "kicad-cli not found")
        return None
    tmp = tempfile.mkdtemp(prefix="pcbcheck_drc_")
    out_json = os.path.join(tmp, "drc.json")
    sch = os.path.splitext(board_path)[0] + ".kicad_sch"
    base = [cli, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", out_json]
    attempts = []
    if os.path.exists(sch):
        attempts.append(base + ["--refill-zones", "--schematic-parity", board_path])
    attempts.append(base + ["--refill-zones", board_path])
    attempts.append(base + [board_path])
    data = None
    last_err = ""
    for cmd in attempts:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **_NOWIN)
        except subprocess.TimeoutExpired:
            last_err = "DRC took too long"
            break
        except OSError as e:
            last_err = str(e)
            break
        if os.path.exists(out_json):
            try:
                with open(out_json, encoding="utf-8") as fh:
                    data = json.load(fh)
                break
            except ValueError:
                pass
        last_err = (res.stderr or res.stdout or "").strip()[-400:]
    shutil.rmtree(tmp, ignore_errors=True)
    if data is None:
        report.skip(cid, f"kicad-cli DRC failed: {last_err or 'no output'}")
        report.skip("DRC-UNROUTED", "DRC did not run")
        report.skip("DRC-PARITY", "DRC did not run")
        return None

    groups = {}
    for v in data.get("violations", []):
        sev = v.get("severity", "error")
        if sev == "exclusion" or v.get("excluded"):
            continue
        key = (v.get("type", "drc"), sev)
        groups.setdefault(key, []).append(v)
    for (typ, sev), lst in sorted(groups.items(), key=lambda kv: (kv[0][1] != "error", kv[0][0])):
        locs = []
        for v in lst[:40]:
            items = v.get("items", [])
            if items:
                pos = items[0].get("pos", {})
                label = " / ".join(i.get("description", "")[:60] for i in items[:2])
                locs.append((pos.get("x", 0.0), pos.get("y", 0.0), "", label))
        desc = lst[0].get("description", typ)
        if typ in _INFO_ONLY:
            sev = "info"
        report.add(cid, "error" if sev == "error" else "warning" if sev == "warning" else "info",
                   f"{len(lst)} x {desc} ({typ})", locs, title=f"KiCad DRC: {desc}",
                   fix=_DRC_HINTS.get(typ, "Open the DRC window in KiCad (Inspect > Design Rules Checker) to see each one."))
    un = data.get("unconnected_items", [])
    if un:
        locs = []
        for v in un[:40]:
            items = v.get("items", [])
            if items:
                pos = items[0].get("pos", {})
                locs.append((pos.get("x", 0.0), pos.get("y", 0.0), "", " / ".join(i.get("description", "")[:60] for i in items[:2])))
        report.add("DRC-UNROUTED", "error", f"{len(un)} connection(s) are not routed yet (ratsnest lines left).", locs,
                   fix="Route them, or check that the zones are filled (B) if they should connect through a pour.")
    par = data.get("schematic_parity", [])
    if par:
        locs = []
        for v in par[:40]:
            items = v.get("items", [])
            pos = items[0].get("pos", {}) if items else {}
            locs.append((pos.get("x", 0.0), pos.get("y", 0.0), "", v.get("description", "")[:80]))
        report.add("DRC-PARITY", "error", f"{len(par)} difference(s) between the board and the schematic.", locs,
                   fix="Tools > Update PCB from Schematic (F8), then check again.")
    elif not os.path.exists(sch):
        report.skip("DRC-PARITY", "no schematic next to the board")
    return data


_INFO_ONLY = {"lib_footprint_mismatch", "lib_footprint_issues", "footprint_symbol_mismatch", "text_height",
              "text_thickness", "silk_edge_clearance"}

_DRC_HINTS = {
    "clearance": "Two different nets are too close. Move the copper apart.",
    "shorting_items": "Two different nets touch: this is a short circuit.",
    "tracks_crossing": "Tracks of different nets cross on the same layer: short circuit.",
    "unconnected_items": "Route the missing connections.",
    "courtyards_overlap": "Two parts overlap. Move them apart.",
    "silk_over_copper": "Silkscreen on a pad is not printed. Move the text or line off the pad.",
    "silk_overlap": "Overlapping silkscreen is unreadable. Move one of them.",
    "copper_edge_clearance": "Copper too close to the board edge.",
    "hole_clearance": "Copper too close to a hole.",
    "lib_footprint_mismatch": "The footprint differs from the library. Usually harmless; update it if you changed the library.",
    "lib_footprint_issues": "The footprint's library could not be found. Usually harmless for manufacturing.",
    "starved_thermal": "A pad connects to a pour with too few thermal spokes.",
    "isolated_copper": "A piece of pour is not connected to anything. Remove it or stitch it with vias.",
}
