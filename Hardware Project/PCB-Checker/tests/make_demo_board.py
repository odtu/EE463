"""Build examples/demo_buck/demo_buck.kicad_pcb: a small EE463-style synchronous buck
(48 V -> 12 V, 2 layers) with typical student mistakes left in on purpose, so the
checker has something to find:

  1. input track only 0.6 mm wide for ~3.5 A            (PWR-WIDTH)
  2. C2 rated 50 V on the 48 V input; C5 10 V on 12 V    (PWR-CAPV)
  3. gate driver U1 far from Q1/Q2, long gate tracks     (PWR-GATE)
  4. feedback divider far from FB, FB track next to SW   (PWR-FB)
  5. NTC track running under the inductor                (PWR-MAG)
  6. no test points on the gate signals                  (TST-POINTS)
  7. a 0402 resistor                                     (ASM-SMALL)
  8. input ceramic C1 far from the low-side source       (PWR-LOOP)
  9. Q1 drain tab without a copper pour                  (PWR-THERMAL)
 10. no voltage/polarity label at the output connector   (PWR-CONN)
 11. low-side source reaches ground through one via      (PWR-WIDTH on GND)

Run with KiCad's Python:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tests/make_demo_board.py
"""

import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                      os.path.join(HERE, "..", "examples", "demo_buck", "demo_buck.kicad_pcb"))
FP_ROOT = os.path.join(os.path.dirname(sys.executable), "..", "share", "kicad", "footprints")


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(2)
nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def place(lib, name, ref, value, x, y, rot=0, pins=None):
    fp = pcbnew.FootprintLoad(os.path.join(FP_ROOT, lib + ".pretty"), name)
    if fp is None:
        raise SystemExit(f"footprint {lib}:{name} not found")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetFPIDAsString(f"{lib}:{name}")
    board.Add(fp)
    fp.SetPosition(pt(x, y))
    fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        info = (pins or {}).get(p.GetNumber())
        if info:
            netname, func = info if isinstance(info, tuple) else (info, "")
            p.SetNet(net(netname))
            if func:
                p.SetPinFunction(func)
                p.SetPinType("power_in" if func in ("VIN", "VCC") else "passive")
    return fp


def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError(num)


def pos(p):
    v = p.GetPosition()
    return round(pcbnew.ToMM(v.x), 4), round(pcbnew.ToMM(v.y), 4)


def track(points, width, netname, layer=pcbnew.F_Cu):
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pt(x1, y1))
        t.SetEnd(pt(x2, y2))
        t.SetWidth(mm(width))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        board.Add(t)


def via(x, y, netname, drill=0.3, size=0.6):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetDrill(mm(drill))
    v.SetWidth(mm(size))
    v.SetNet(net(netname))
    board.Add(v)


def gnd_via(p, dx=0.0, dy=0.0, w=0.5):
    x, y = pos(p)
    via(x + dx, y + dy, "GND")
    track([(x, y), (x + dx, y + dy)], w, "GND")


def zone(netname, layer, pts, thermal=True):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net(netname))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(x), mm(y))
    z.SetMinThickness(mm(0.25))
    z.SetLocalClearance(mm(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(mm(0.5))
    z.SetThermalReliefSpokeWidth(mm(0.5))
    board.Add(z)
    return z


def text(s, x, y, size=1.2, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.18))
    board.Add(t)


B = pcbnew.B_Cu

# --- outline 80 x 60 mm --------------------------------------------------------
X0, Y0, X1, Y1 = 100, 100, 180, 160
for (a, b) in [((X0, Y0), (X1, Y0)), ((X1, Y0), (X1, Y1)), ((X1, Y1), (X0, Y1)), ((X0, Y1), (X0, Y0))]:
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a))
    s.SetEnd(pt(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)

# --- parts ----------------------------------------------------------------------
TB = "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
J1 = place("TerminalBlock_Phoenix", TB, "J1", "VIN", 106, 118, 90, {"1": "VIN", "2": "GND"})
J2 = place("TerminalBlock_Phoenix", TB, "J2", "VOUT", 174, 113, 270, {"1": "VOUT", "2": "GND"})
Q1 = place("Package_TO_SOT_SMD", "TO-252-2", "Q1", "BSC100N10", 132, 112, 0,
           {"1": ("GH", "G"), "2": ("VIN", "D"), "3": ("SW", "S")})
Q2 = place("Package_TO_SOT_SMD", "TO-252-2", "Q2", "BSC100N10", 132, 132, 0,
           {"1": ("GL", "G"), "2": ("SW", "D"), "3": ("GND", "S")})
L1 = place("Inductor_SMD", "L_12x12mm_H8mm", "L1", "15uH 10A", 155, 122, 0, {"1": "SW", "2": "VOUT"})
U1 = place("Package_SO", "SOIC-14_3.9x8.7mm_P1.27mm", "U1", "LM5145", 112, 146, 0, {
    "1": ("VIN", "VIN"), "2": ("EN", "EN"), "3": ("FB", "FB"), "4": ("COMP", "COMP"), "5": ("GND", "AGND"),
    "6": ("VCC", "VCC"), "7": ("HO_R", "HO"), "8": ("SW", "SW"), "9": ("HB", "HB"), "10": ("LO_R", "LO"),
    "11": ("GND", "PGND"), "12": ("RT", "RT"), "13": ("SS", "SS"), "14": ("PGOOD", "PGOOD")})
C1 = place("Capacitor_SMD", "C_1210_3225Metric", "C1", "4.7uF 100V", 141, 117, 270, {"1": "VIN", "2": "GND"})
C2 = place("Capacitor_SMD", "C_1210_3225Metric", "C2", "4.7uF 50V", 121, 108, 0, {"1": "VIN", "2": "GND"})
C3 = place("Capacitor_THT", "CP_Radial_D10.0mm_P5.00mm", "C3", "100uF 63V", 116, 120, 0, {"1": "VIN", "2": "GND"})
C4 = place("Capacitor_SMD", "C_1210_3225Metric", "C4", "47uF 25V", 166, 126, 0, {"1": "VOUT", "2": "GND"})
C5 = place("Capacitor_THT", "CP_Radial_D8.0mm_P3.50mm", "C5", "470uF 10V", 160, 145, 0, {"1": "VOUT", "2": "GND"})
C6 = place("Capacitor_SMD", "C_0603_1608Metric", "C6", "100nF 25V", 117.5, 150.5, 270, {"1": "HB", "2": "SW"})
C7 = place("Capacitor_SMD", "C_0603_1608Metric", "C7", "1uF 25V", 106, 148.54, 180, {"1": "VCC", "2": "GND"})
C8 = place("Capacitor_SMD", "C_0603_1608Metric", "C8", "100nF 100V", 104, 135, 270, {"1": "VIN", "2": "GND"})
R1 = place("Resistor_SMD", "R_0603_1608Metric", "R1", "100k", 150, 150, 0, {"1": "VOUT", "2": "FB"})
R2 = place("Resistor_SMD", "R_0402_1005Metric", "R2", "7.15k", 150, 154, 0, {"1": "FB", "2": "GND"})
R3 = place("Resistor_SMD", "R_0603_1608Metric", "R3", "2.2", 110.36, 152.5, 0, {"1": "HO_R", "2": "GH"})
R4 = place("Resistor_SMD", "R_0603_1608Metric", "R4", "2.2", 118.5, 147.27, 0, {"1": "LO_R", "2": "GL"})
RT1 = place("Resistor_SMD", "R_0603_1608Metric", "RT1", "10k NTC", 155, 134, 270, {"1": "NTC", "2": "GND"})
TP1 = place("TestPoint", "TestPoint_Pad_D1.5mm", "TP1", "GND", 140, 152, 0, {"1": "GND"})
TP2 = place("TestPoint", "TestPoint_Pad_D1.5mm", "TP2", "VCC", 109, 154.5, 0, {"1": "VCC"})
TP3 = place("TestPoint", "TestPoint_Pad_D1.5mm", "TP3", "NTC", 155, 108, 0, {"1": "NTC"})
for i, (x, y) in enumerate([(104, 104), (176, 104), (104, 156), (176, 156)], 1):
    place("MountingHole", "MountingHole_3.2mm_M3", f"H{i}", "M3", x, y)

# --- input side (mistake 1: 0.6 mm) ----------------------------------------------
track([pos(pad(J1, "1")), (114, 118), pos(pad(C3, "1"))], 0.6, "VIN")
track([pos(pad(C3, "1")), (116, 116), (120, 112), pos(pad(Q1, "2"))], 0.6, "VIN")
track([pos(pad(C2, "1")), (pos(pad(C2, "1"))[0], 112.47)], 0.6, "VIN")
track([pos(pad(Q1, "2")), (137.5, 112), pos(pad(C1, "1"))], 2.0, "VIN")
track([pos(pad(C8, "1")), (104, 120), pos(pad(J1, "1"))], 0.3, "VIN")
track([pos(pad(U1, "1")), (106.5, 139.16), (106.5, 130), (104, 127.5)], 0.3, "VIN")
gnd_via(pad(C1, "2"), 2.0)
gnd_via(pad(C2, "2"), 0, -2.0)
gnd_via(pad(C8, "2"), 0, 1.2)

# --- switch node pour, inductor, output ----------------------------------------------
zone("SW", pcbnew.F_Cu, [(125.5, 113.4), (130, 113.4), (130, 120), (152.6, 120), (152.6, 124), (138, 124),
                         (138, 135.6), (129.6, 135.6), (129.6, 126), (125.5, 121.9)], thermal=False)
track([pos(pad(L1, "2")), (163, 122), (169, 116), (169, 113), pos(pad(J2, "1"))], 3.0, "VOUT")
track([pos(pad(C4, "1")), (164.53, 123.5), (163, 122)], 1.5, "VOUT")
track([pos(pad(C5, "1")), (160, 124), (160, 122.5)], 1.5, "VOUT")
gnd_via(pad(C4, "2"), 1.2)
gnd_via(pad(C5, "2"), 0, -1.3)
gnd_via(pad(Q2, "3"), -2.16)

# --- controller, gate drive (mistake 3: far away, long gate tracks) ------------------
track([pos(pad(U1, "10")), pos(pad(R4, "1"))], 0.4, "LO_R")
track([pos(pad(R4, "2")), (120.5, 147.27)], 0.4, "GL")
via(120.5, 147.27, "GL")
track([(120.5, 147.27), (120.5, 131.67), (122.45, 129.72), (124.8, 129.72)], 0.4, "GL", B)
via(124.8, 129.72, "GL")
track([(124.8, 129.72), pos(pad(Q2, "1"))], 0.4, "GL")

track([pos(pad(U1, "7")), pos(pad(R3, "1"))], 0.4, "HO_R")
track([pos(pad(R3, "2")), (112.49, 151.2)], 0.4, "GH")
via(112.49, 151.2, "GH")
track([(112.49, 151.2), (102.6, 151.2), (102.6, 108.5), (124.5, 108.5)], 0.4, "GH", B)
via(124.5, 108.5, "GH")
track([(124.5, 108.5), (125.72, 109.72), pos(pad(Q1, "1"))], 0.4, "GH")

track([pos(pad(U1, "9")), (116.31, 148.54), pos(pad(C6, "1"))], 0.3, "HB")
track([pos(pad(U1, "8")), (115.94, 151.28), pos(pad(C6, "2"))], 0.3, "SW")
track([pos(pad(C6, "2")), (118.72, 152.5), (119.5, 152.5)], 0.3, "SW")
via(119.5, 152.5, "SW")
track([(119.5, 152.5), (119.5, 118.6), (121.5, 116.6), (125.6, 116.6)], 0.5, "SW", B)
via(125.6, 116.6, "SW")

track([pos(pad(C7, "1")), pos(pad(U1, "6"))], 0.3, "VCC")
track([pos(pad(C7, "1")), (106.78, 152.28), pos(pad(TP2, "1"))], 0.3, "VCC")
track([pos(pad(U1, "5")), (105.22, 147.27)], 0.3, "GND")
via(105.22, 147.27, "GND")
track([pos(pad(C7, "2")), (105.22, 147.27)], 0.3, "GND")
gnd_via(pad(U1, "11"), 1.53, 0, 0.3)

# --- feedback (mistake 4) ------------------------------------------------------------
track([pos(pad(R1, "1")), (154.18, 145), pos(pad(C5, "1"))], 0.3, "VOUT")
track([pos(pad(R1, "2")), (150.82, 152.67), pos(pad(R2, "1"))], 0.25, "FB")
track([pos(pad(R2, "1")), (147, 154), (147, 138), (138.5, 138), (137, 136.5), (130, 136.5), (128.5, 138), (116, 138)],
      0.25, "FB")
via(116, 138, "FB")
track([(116, 138), (106.6, 138), (106.6, 144.73)], 0.25, "FB", B)
via(106.6, 144.73, "FB")
track([(106.6, 144.73), pos(pad(U1, "3"))], 0.25, "FB")
gnd_via(pad(R2, "2"), 1.2, 0, 0.3)

# --- NTC under the inductor (mistake 5) ----------------------------------------------
track([pos(pad(TP3, "1")), pos(pad(RT1, "1"))], 0.25, "NTC")
gnd_via(pad(RT1, "2"), 0, 1.3, 0.3)
gnd_via(pad(TP1, "1"), 0, -1.6)

# --- ground pour on the bottom ---------------------------------------------------------
zone("GND", B, [(X0 + 0.5, Y0 + 0.5), (X1 - 0.5, Y0 + 0.5), (X1 - 0.5, Y1 - 0.5), (X0 + 0.5, Y1 - 0.5)])

# --- silkscreen (mistake 10: nothing at J2) ----------------------------------------------
text("VIN 20-48V  + / -", 118, 103.2)
text("EE463 Group 0 - demo board Rev A", 150, 103.2)

board.SetFileName(OUT)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
print("wrote", OUT)
