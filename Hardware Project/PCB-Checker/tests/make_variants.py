"""Build small converter boards of other kinds, to test what the checker recognises.

    python tests/make_variants.py <out_dir>

Writes nonsync_buck, ic_buck, flyback (parts + nets, a few tracks) and demo_nopins
(the demo board with every pin name removed, as when footprints were placed by hand).
Needs KiCad's Python.
"""

import os
import re
import subprocess
import sys

import pcbnew

FP_ROOT = os.path.join(os.path.dirname(sys.executable), "..", "share", "kicad", "footprints")
HERE = os.path.dirname(os.path.abspath(__file__))


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


class Builder:
    def __init__(self):
        self.board = pcbnew.CreateEmptyBoard()
        self.board.SetCopperLayerCount(2)
        self.nets = {}
        for (a, b) in [((100, 100), (160, 100)), ((160, 100), (160, 150)), ((160, 150), (100, 150)), ((100, 150), (100, 100))]:
            s = pcbnew.PCB_SHAPE(self.board)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(pt(*a))
            s.SetEnd(pt(*b))
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(mm(0.1))
            self.board.Add(s)

    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def place(self, lib, name, ref, value, x, y, pins, rot=0):
        fp = pcbnew.FootprintLoad(os.path.join(FP_ROOT, lib + ".pretty"), name)
        if fp is None:
            raise SystemExit(f"missing footprint {lib}:{name}")
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetFPIDAsString(f"{lib}:{name}")
        self.board.Add(fp)
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        for p in fp.Pads():
            info = pins.get(p.GetNumber())
            if info:
                netname, func = info if isinstance(info, tuple) else (info, "")
                p.SetNet(self.net(netname))
                if func:
                    p.SetPinFunction(func)
        return fp

    def save(self, path):
        self.board.SetFileName(path)
        pcbnew.SaveBoard(path, self.board)


def nonsync_buck(path):
    b = Builder()
    b.place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "J1", "IN",
            105, 120, {"1": "VIN", "2": "GND"}, 90)
    b.place("Package_TO_SOT_SMD", "TO-252-2", "Q1", "IPD50N10", 125, 112, {"1": ("GH", "G"), "2": ("VIN", "D"), "3": ("SW", "S")})
    b.place("Diode_SMD", "D_SMC", "D1", "SS510", 125, 128, {"1": ("SW", "K"), "2": ("GND", "A")})
    b.place("Inductor_SMD", "L_12x12mm_H8mm", "L1", "22uH", 142, 120, {"1": "SW", "2": "VOUT"})
    b.place("Capacitor_SMD", "C_1210_3225Metric", "C1", "4.7uF 100V", 118, 120, {"1": "VIN", "2": "GND"}, 90)
    b.place("Capacitor_SMD", "C_1210_3225Metric", "C2", "47uF 25V", 150, 132, {"1": "VOUT", "2": "GND"}, 90)
    b.place("Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm", "U1", "LM5085", 120, 140, {
        "1": ("BST", "BST"), "2": ("VIN", "VIN"), "3": ("EN", "EN"), "4": ("FB", "FB"), "5": ("GND", "GND"),
        "6": ("VCC", "VCC"), "7": ("HO", "HO"), "8": ("SW", "SW")})
    b.place("Resistor_SMD", "R_0805_2012Metric", "R1", "4.7", 122, 132, {"1": "HO", "2": "GH"})
    b.place("Capacitor_SMD", "C_0805_2012Metric", "C3", "100nF 25V", 128, 140, {"1": "BST", "2": "SW"})
    b.place("Resistor_SMD", "R_0805_2012Metric", "R2", "47k", 112, 140, {"1": "VOUT", "2": "FB"})
    b.place("Resistor_SMD", "R_0805_2012Metric", "R3", "4.7k", 112, 143, {"1": "FB", "2": "GND"})
    b.place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "J2", "OUT",
            155, 112, {"1": "VOUT", "2": "GND"}, 270)
    b.save(path)


def ic_buck(path):
    b = Builder()
    b.place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "J1", "IN",
            105, 120, {"1": "+48V", "2": "GND"}, 90)
    b.place("Package_SO", "SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm", "U1", "TPS54560", 125, 120, {
        "1": ("BOOT", "BOOT"), "2": ("+48V", "VIN"), "3": ("EN", "EN"), "4": ("RT", "RT/CLK"), "5": ("FB", "FB"),
        "6": ("COMP", "COMP"), "7": ("GND", "GND"), "8": ("LX", "SW"), "9": ("GND", "PAD")})
    b.place("Capacitor_SMD", "C_1210_3225Metric", "C1", "2.2uF 100V", 118, 120, {"1": "+48V", "2": "GND"}, 90)
    b.place("Capacitor_SMD", "C_0805_2012Metric", "C2", "100nF 25V", 131, 116, {"1": "BOOT", "2": "LX"})
    b.place("Inductor_SMD", "L_12x12mm_H8mm", "L1", "22uH", 142, 120, {"1": "LX", "2": "+12V"})
    b.place("Capacitor_SMD", "C_1210_3225Metric", "C3", "47uF 25V", 152, 132, {"1": "+12V", "2": "GND"}, 90)
    b.place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "J2", "OUT",
            155, 112, {"1": "+12V", "2": "GND"}, 270)
    b.save(path)


def flyback(path):
    b = Builder()
    b.place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "J1", "IN",
            105, 120, {"1": "VIN", "2": "GND"}, 90)
    t = b.place("Transformer_SMD", "Pulse_PA2002NL-PA2008NL-PA2009NL", "T1", "PA2008NL", 130, 120, {})
    nums = sorted({p.GetNumber() for p in t.Pads() if p.GetNumber()}, key=lambda s: int(re.sub(r"\D", "", s) or 0))
    for num, n in zip(nums, ["VIN", "DRAIN", "SEC", "GND_ISO"]):
        for p in t.Pads():
            if p.GetNumber() == num:
                p.SetNet(b.net(n))
    b.place("Package_TO_SOT_SMD", "TO-252-2", "Q1", "IPD60R", 118, 132, {"1": ("GATE", "G"), "2": ("DRAIN", "D"), "3": ("CS", "S")})
    b.place("Resistor_SMD", "R_2512_6332Metric", "R1", "0.05", 118, 142, {"1": "CS", "2": "GND"})
    b.place("Diode_SMD", "D_SMC", "D1", "SS510", 142, 118, {"1": ("VOUT", "K"), "2": ("SEC", "A")})
    b.place("Capacitor_SMD", "C_1210_3225Metric", "C1", "4.7uF 100V", 112, 120, {"1": "VIN", "2": "GND"}, 90)
    b.place("Capacitor_SMD", "C_1210_3225Metric", "C2", "47uF 25V", 150, 125, {"1": "VOUT", "2": "GND_ISO"}, 90)
    b.place("Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm", "U1", "UCC28C44", 105, 138, {
        "1": ("COMP", "COMP"), "2": ("FB", "FB"), "3": ("CS", "CS"), "4": ("RT", "RT/CT"), "5": ("GND", "GND"),
        "6": ("GDRV", "OUT"), "7": ("VCC", "VDD"), "8": ("VREF", "VREF")})
    b.place("Resistor_SMD", "R_0805_2012Metric", "R2", "10", 112, 134, {"1": "GDRV", "2": "GATE"})
    b.place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "J2", "OUT",
            155, 112, {"1": "VOUT", "2": "GND_ISO"}, 270)
    b.save(path)


def demo_nopins(path):
    tmp = path + ".tmp.kicad_pcb"
    subprocess.run([sys.executable, os.path.join(HERE, "make_demo_board.py"), tmp], check=True, capture_output=True)
    text = open(tmp, encoding="utf-8").read()
    text = re.sub(r'\s*\(pinfunction "[^"]*"\)', "", text)
    text = re.sub(r'\s*\(pintype "[^"]*"\)', "", text)
    open(path, "w", encoding="utf-8").write(text)
    for ext in (".kicad_pcb", ".kicad_pro", ".kicad_prl"):
        p = path + ".tmp" + ext
        if os.path.exists(p):
            os.remove(p)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for fn in (nonsync_buck, ic_buck, flyback, demo_nopins):
        p = os.path.join(out, fn.__name__ + ".kicad_pcb")
        fn(p)
        print("wrote", p)
