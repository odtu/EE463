"""Run only the Gerber/drill checks on folders or zips (one per argument)."""

import glob
import os
import shutil
import sys
import tempfile
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pcbcheck.gerber import load_fab_files, is_fab_file  # noqa: E402
from pcbcheck.checks_gerber import run_gerber_checks  # noqa: E402
from pcbcheck.findings import Report  # noqa: E402
from pcbcheck.cli import _safe_extract, _walk  # noqa: E402

for target in sys.argv[1:]:
    tmp = None
    folder = target
    if target.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp()
        _safe_extract(target, tmp)
        folder = tmp
    files = [f for f in _walk(folder) if is_fab_file(f) and not f.endswith((".kicad_pcb", ".kicad_sch"))]
    print("=" * 100)
    print(target, f"({len(files)} files)")
    t = time.time()
    try:
        fs = load_fab_files(files)
        for l in fs.layers:
            if l.kind not in ("extra",):
                print(f"   {l.kind:14s} {l.name:45s} draws={len(l.draws)} arcs={len(l.arcs)} flashes={len(l.flashes)} "
                      f"regions={len(l.regions)} units={l.units} bbox={tuple(round(v, 1) for v in (l.bbox() or ()))}")
        for d in fs.drills:
            sizes = sorted({round(h[2], 3) for h in d.holes})
            print(f"   {d.kind:14s} {d.name:45s} holes={len(d.holes)} slots={len(d.slots)} sizes={sizes[:10]} "
                  f"plated={sum(1 for h in d.holes if h[3])}")
        r = Report()
        run_gerber_checks(fs, r)
        print(f"   -> {r.counts()} in {time.time() - t:.1f}s")
        for f in r.findings():
            print(f"   [{f.severity}] {f.check}: {f.message[:170]}  {f.locations[:2]}")
    except Exception:
        traceback.print_exc()
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
