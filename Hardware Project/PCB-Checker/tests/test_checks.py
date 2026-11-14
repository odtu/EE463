"""Tests. Run with KiCad's Python (or any Python 3.8+):

    python -m unittest discover -s tests -v
"""

import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pcbcheck.findings import Report  # noqa: E402
from pcbcheck.analysis import cap_farads, res_ohms  # noqa: E402
from pcbcheck.geometry import Shape, distance, ipc2221_width, ipc2221_rise  # noqa: E402
from pcbcheck import sexpr  # noqa: E402

try:
    import pcbnew  # noqa: F401  (KiCad's Python: the demo board is rebuilt fresh for the tests)
    HAVE_PCBNEW = True
except ImportError:
    HAVE_PCBNEW = False

GERBER_HEAD = """%TF.FileFunction,Copper,L1,Top*%
%FSLAX46Y46*%
%MOMM*%
%LPD*%
%ADD10C,0.100000*%
%ADD11C,0.300000*%
%ADD12C,1.000000*%
"""

TOP = GERBER_HEAD + """%TO.N,A*%
D10*
X10000000Y-10000000D02*
X30000000Y-10000000D01*
%TD*%
%TO.N,B*%
D11*
X10000000Y-12000000D02*
X30000000Y-12000000D01*
%TD*%
%TO.N,C*%
D11*
X10000000Y-12400000D02*
X30000000Y-12400000D01*
%TD*%
%TO.N,D*%
D11*
X10000000Y-20000000D02*
X10000000Y-29900000D01*
%TD*%
%TO.N,E*%
D12*
X5000000Y-5000000D03*
%TD*%
M02*
"""

BOTTOM = TOP.replace("L1,Top", "L2,Bot")

OUTLINE = """%TF.FileFunction,Profile,NP*%
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.100000*%
D10*
X0Y0D02*
X40000000Y0D01*
X40000000Y-30000000D01*
X0Y-30000000D01*
X0Y0D01*
M02*
"""

DRILL = """M48
; #@! TF.FileFunction,Plated,1,2,PTH
METRIC
T1C0.200
T2C0.400
%
G90
G05
T1
X35.0Y-25.0
T2
X5.0Y-5.0
M30
"""


class TestUnits(unittest.TestCase):
    def test_values(self):
        self.assertAlmostEqual(cap_farads("100nF"), 100e-9)
        self.assertAlmostEqual(cap_farads("4u7"), 4.7e-6)
        self.assertAlmostEqual(cap_farads("22 µF 63V"), 22e-6)
        self.assertAlmostEqual(res_ohms("0R01"), 0.01)
        self.assertAlmostEqual(res_ohms("10m"), 0.01)
        self.assertAlmostEqual(res_ohms("4k7"), 4700)
        self.assertAlmostEqual(res_ohms("100k"), 100e3)

    def test_ipc2221(self):
        # lab table: 5 A on 1 oz outer at 10 degC rise -> about 2.8 mm
        self.assertAlmostEqual(ipc2221_width(5, 10), 2.76, places=1)
        self.assertAlmostEqual(ipc2221_rise(5, ipc2221_width(5, 20)), 20, places=3)

    def test_distance(self):
        a = Shape.segment(0, 0, 10, 0, 0.1)
        b = Shape.segment(0, 1, 10, 1, 0.1)
        self.assertAlmostEqual(distance(a, b), 0.8)
        self.assertEqual(distance(Shape.rect(0, 0, 2, 2), Shape.point(0.5, 0.5, 0.1)), 0.0)

    def test_sexpr(self):
        n = sexpr.parse('(a (b 1 2) (c "x y") (net 3 "GND"))')
        self.assertEqual(sexpr.xy(n, "b"), (1.0, 2.0))
        self.assertEqual(sexpr.value(n, "c"), "x y")


class TestGerber(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for name, text in (("t-F_Cu.gtl", TOP), ("t-B_Cu.gbl", BOTTOM), ("t-Edge_Cuts.gm1", OUTLINE), ("t.drl", DRILL)):
            with open(os.path.join(self.dir, name), "w") as fh:
                fh.write(text)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_finds_problems(self):
        from pcbcheck.gerber import load_fab_files
        from pcbcheck.checks_gerber import run_gerber_checks
        fs = load_fab_files([os.path.join(self.dir, f) for f in os.listdir(self.dir)])
        r = Report()
        run_gerber_checks(fs, r)
        status = {c: r.checks[c].status for c in r.order}
        self.assertEqual(status["GBR-TRACK"], "error")   # 0.1 mm track
        self.assertEqual(status["GBR-CLEAR"], "error")   # nets B and C 0.1 mm apart
        self.assertEqual(status["GBR-DRILL"], "error")   # 0.2 mm hole
        self.assertEqual(status["GBR-EDGE"], "error")    # track D ends at the edge
        self.assertEqual(status["GBR-RING"], "pass")     # 1.0 pad on 0.4 hole
        clear = r.checks["GBR-CLEAR"].findings[0]
        self.assertIn("B / C", " ".join(l[3] for l in clear.locations))


MINI_PCB = """(kicad_pcb (version 20241229) (generator "pcbnew")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (footprint "Test:QFP" (layer "F.Cu") (at 10 10 90)
    (property "Reference" "U1" (at 0 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0 -5) (size 1.5 0.25) (layers "F.Cu") (net "A"))
    (pad "2" smd rect (at 0 -3 90) (size 1.5 0.25) (layers "F.Cu") (net "B")))
)
"""

ALLEGRO_TOP = """G04 Cadence Allegro*
%FSLAX55Y55*MOIN*%
%ADD10C,.01*%
%ADD11C,.06*%
G01*
D10*
X0Y0D02*
X100000Y0D01*
D11*
X50000Y50000D03*
M02*
"""

ALLEGRO_DRILL = """;FILE  : board-1-2.drl
;T01 Holesize 1. = 16.000000 Tolerance = +0.000000/-0.000000 PLATED MILS Quantity = 1
%
G90
T01
X50000Y50000
M30
"""


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class TestRegressions(unittest.TestCase):
    def test_pad_angle_default_is_zero(self):
        # KiCad omits the angle of a pad whose absolute orientation is 0, even on a rotated footprint
        from pcbcheck.kicad_board import load_board
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "mini.kicad_pcb")
            _write(p, MINI_PCB)
            b = load_board(p)
            pads = {q.number: q for q in b.fp("U1").pads}
            self.assertEqual(pads["1"].angle, 0.0)
            self.assertEqual(pads["2"].angle, 90.0)
            x0, y0, x1, y1 = pads["1"].geom.bbox
            self.assertAlmostEqual(x1 - x0, 1.5, places=3)   # 1.5 mm along X, not rotated
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_allegro_files(self):
        from pcbcheck.gerber import load_fab_files
        d = tempfile.mkdtemp()
        try:
            for name, text in (("TOP.art", ALLEGRO_TOP), ("BOTTOM.art", ALLEGRO_TOP), ("board-1-2.drl", ALLEGRO_DRILL)):
                _write(os.path.join(d, name), text)
            fs = load_fab_files([os.path.join(d, f) for f in os.listdir(d)])
            kinds = sorted(l.kind for l in fs.layers)
            self.assertEqual(kinds, ["copper_bottom", "copper_top"])
            top = fs.by_kind("copper_top")[0]
            self.assertEqual(top.units, "in")
            self.assertAlmostEqual(top.draws[0][2], 25.4, places=3)        # 1 inch long line
            self.assertAlmostEqual(top.draws[0][4], 0.254, places=3)       # 10 mil wide
            hole = fs.drills[0].holes[0]
            self.assertAlmostEqual(hole[2], 0.4064, places=3)              # 16 mil from the comment
            self.assertAlmostEqual(hole[0], 12.7, places=2)                # format guessed: 0.5 inch
            self.assertTrue(fs.drills[0].format_unknown)
        finally:
            shutil.rmtree(d, ignore_errors=True)


@unittest.skipUnless(HAVE_PCBNEW, "needs KiCad's Python to build the demo board")
class TestDemoBoard(unittest.TestCase):
    """A freshly built demo board has known mistakes; each must be found, and nothing else.
    (examples/demo_buck may have been edited by hand, so it is not used here.)"""

    @classmethod
    def setUpClass(cls):
        import subprocess
        from pcbcheck.kicad_board import load_board
        from pcbcheck.checks_kicad import run_kicad_checks
        cls.tmp = tempfile.mkdtemp()
        demo = os.path.join(cls.tmp, "demo_buck.kicad_pcb")
        subprocess.run([sys.executable, os.path.join(ROOT, "tests", "make_demo_board.py"), demo],
                       check=True, capture_output=True)
        cls.r = Report()
        cls.c = run_kicad_checks(load_board(demo), cls.r)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def status(self, cid):
        return self.r.checks[cid].status

    def text(self, cid):
        return " ".join(f.message for f in self.r.checks[cid].findings)

    def test_detection(self):
        a = self.c.a
        self.assertIn("synchronous buck", a.topology())
        self.assertEqual(a.sw, {"SW"})
        self.assertEqual(a.input, {"VIN"})
        self.assertEqual(a.output, {"VOUT"})
        self.assertEqual({g.driver.ref for g in a.gates}, {"U1"})
        self.assertEqual([c.ref for c, _, _ in a.bootstrap], ["C6"])

    def test_planted_mistakes(self):
        self.assertEqual(self.status("PWR-WIDTH"), "error")
        self.assertIn("VIN", self.text("PWR-WIDTH"))
        self.assertIn("C5", self.text("PWR-CAPV"))
        self.assertIn("C2", self.text("PWR-CAPV"))
        self.assertNotIn("C6", self.text("PWR-CAPV"))      # bootstrap cap sees only VCC
        self.assertIn("Q1", self.text("PWR-GATE"))
        self.assertIn("R1", self.text("PWR-FB"))
        self.assertIn("NTC", self.text("PWR-MAG"))
        self.assertIn("Q2", self.text("PWR-LOOP"))
        self.assertIn("Q1", self.text("PWR-THERMAL"))
        self.assertIn("J2", self.text("PWR-CONN"))
        self.assertIn("gate signal", self.text("TST-POINTS"))
        self.assertIn("R2", self.text("ASM-SMALL"))

    def test_no_false_alarms(self):
        for cid in ("FAB-TRACK", "FAB-CLEAR", "FAB-DRILL", "FAB-RING", "FAB-HOLES", "FAB-EDGE",
                    "PWR-SPACING", "LAY-ACUTE", "LAY-DANGLE", "LAY-VIAPAD", "ASM-SPACING"):
            self.assertEqual(self.status(cid), "pass", f"{cid}: {self.text(cid)}")
        self.assertNotIn("SW", self.text("PWR-VIAS"))


@unittest.skipUnless(HAVE_PCBNEW, "needs KiCad's Python to build the variant boards")
class TestVariants(unittest.TestCase):
    """Other converter kinds a group may build: the checker must recognise each one."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        from pcbcheck.kicad_board import load_board
        from pcbcheck.analysis import Analysis
        cls.tmp = tempfile.mkdtemp()
        subprocess.run([sys.executable, os.path.join(ROOT, "tests", "make_variants.py"), cls.tmp],
                       check=True, capture_output=True)
        cls.a = {n: Analysis(load_board(os.path.join(cls.tmp, n + ".kicad_pcb")))
                 for n in ("nonsync_buck", "ic_buck", "flyback", "demo_nopins")}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_nonsync_buck(self):
        a = self.a["nonsync_buck"]
        self.assertIn("non-synchronous buck", a.topology())
        self.assertEqual([f.ref for f in a.power_diodes], ["D1"])
        self.assertEqual((a.sw, a.input, a.output), ({"SW"}, {"VIN"}, {"VOUT"}))
        self.assertEqual([c.ref for c, _, _ in a.bootstrap], ["C3"])

    def test_ic_buck(self):
        a = self.a["ic_buck"]
        self.assertIn("integrated switch", a.topology())
        self.assertEqual((a.sw, a.input, a.output), ({"LX"}, {"+48V"}, {"+12V"}))

    def test_flyback(self):
        a = self.a["flyback"]
        self.assertIn("isolated", a.topology())
        self.assertIn("VIN", a.input)
        self.assertIn("VOUT", a.output)
        self.assertEqual({g.driver.ref for g in a.gates if g.driver}, {"U1"})

    def test_no_pin_names(self):
        a = self.a["demo_nopins"]
        self.assertIn("synchronous buck", a.topology())
        self.assertEqual((a.sw, a.input, a.output), ({"SW"}, {"VIN"}, {"VOUT"}))
        self.assertEqual({g.driver.ref for g in a.gates if g.driver}, {"U1"})
        self.assertEqual([c.ref for c, _, _ in a.bootstrap], ["C6"])


if __name__ == "__main__":
    unittest.main()
