"""Run the checker (without KiCad DRC) on many boards to find crashes, slow checks
and suspicious findings.

    python tests/batch_run.py <list.txt with one .kicad_pcb or folder per line> <out_dir>
"""

import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pcbcheck import cli  # noqa: E402


def main():
    lst, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    targets = [l.strip() for l in open(lst, encoding="utf-8") if l.strip() and not l.startswith("#")]
    summary = []
    for i, t in enumerate(targets):
        name = f"{i:02d}_" + os.path.splitext(os.path.basename(t.rstrip("/\\")))[0][:40]
        rec = {"target": t, "name": name}
        t0 = time.time()
        timings = {}
        try:
            import pcbcheck.checks_kicad as ck
            orig = list(ck.ALL_CHECKS)

            def timed(fn):
                def w(c):
                    s = time.time()
                    try:
                        return fn(c)
                    finally:
                        timings[fn.__name__] = round(time.time() - s, 2)
                w.__name__ = fn.__name__
                return w
            ck.ALL_CHECKS[:] = [timed(f) for f in orig]
            try:
                r = cli.run(t, out=os.path.join(out, name + ".html"), drc=False, quiet=True)
            finally:
                ck.ALL_CHECKS[:] = orig
            rec["time"] = round(time.time() - t0, 1)
            rec["counts"] = r.counts()
            rec["slow"] = {k: v for k, v in timings.items() if v > 2}
            rec["internal"] = [f.message for f in r.findings() if f.check.startswith("INTERNAL")]
            rec["detected"] = r.detected
            rec["findings"] = [(f.check, f.severity, f.message[:200]) for f in r.findings()]
        except BaseException as e:  # noqa: B036
            rec["crash"] = traceback.format_exc()[-1500:]
            rec["time"] = round(time.time() - t0, 1)
        summary.append(rec)
        status = "CRASH" if "crash" in rec else f"{rec['counts']} slow={rec['slow']} internal={len(rec['internal'])}"
        print(f"{name:45s} {rec['time']:6.1f}s {status}", flush=True)
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
