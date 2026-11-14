"""Find what is on a KiCad board: the converter's power parts and the role of each net.

Everything here is a guess from reference designators, footprints, values,
pin names and connections. The report prints what was found so students can
check it, and pcb_checker.json can correct the net roles.
"""

import re
from collections import defaultdict

from .rules import PROJECT, POWER

# ---------------------------------------------------------------------------
# Value parsing


def cap_farads(value):
    s = value.replace("µ", "u").replace("μ", "u").replace(" ", "").lower()
    m = re.match(r"^(\d+(?:[.,]\d+)?)([pnum])(\d*)", s)
    if m:
        num = float(m.group(1).replace(",", "."))
        if m.group(3):
            num = float(f"{m.group(1).replace(',', '.')}{'' if '.' in m.group(1) else '.'}{m.group(3)}") \
                if "." not in m.group(1) else num
        return num * {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}[m.group(2)]
    m = re.match(r"^(\d+(?:\.\d+)?)f", s)
    if m:
        return float(m.group(1))
    return None


def res_ohms(value):
    s = value.replace("Ω", "").replace("ohms", "").replace("Ohms", "").replace("ohm", "") \
        .replace("Ohm", "").replace(" ", "")
    m = re.match(r"^(\d*)([RrkKmM])(\d*)$", s)
    if m and (m.group(1) or m.group(3)):
        a, unit, b = m.groups()
        num = float(f"{a or '0'}.{b or '0'}")
        return num * {"R": 1, "r": 1, "k": 1e3, "K": 1e3, "m": 1e-3, "M": 1e6}[unit]
    m = re.match(r"^(\d+(?:\.\d+)?)([RrkKmM]?)", s)
    if m:
        num = float(m.group(1))
        return num * {"": 1, "R": 1, "r": 1, "k": 1e3, "K": 1e3, "m": 1e-3, "M": 1e6}[m.group(2)]
    return None


def voltage_rating(fp):
    """Voltage rating from the part's fields, if any field states one."""
    for key, val in fp.props.items():
        if key in ("Reference", "Footprint", "Datasheet", "ki_fp_filters"):
            continue
        if re.search(r"volt|rating|^v$|vdc", key, re.I):
            m = re.match(r"^\s*(\d+(?:[.,]\d+)?)\s*(V|VDC)?\s*$", val, re.I)
            if m:
                return float(m.group(1).replace(",", "."))
        m = re.search(r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*V(?:DC)?\b", val)
        if m and key in ("Value", "Description", "Voltage", "Rating", "Voltage Rating"):
            return float(m.group(1).replace(",", "."))
    return None


def base_name(net):
    return net.rsplit("/", 1)[-1].upper()


def fmt_cap(f):
    if f is None:
        return "?"
    for unit, k in (("µF", 1e-6), ("nF", 1e-9), ("pF", 1e-12)):
        if f >= k:
            return f"{f / k:g} {unit}"
    return f"{f:g} F"


GND_RE = re.compile(r"GND|VSS|^0V$|^COM$|RETURN|^RTN|^AGND|^PGND")
IN_RE = re.compile(r"(^|[^A-Z])(V_?IN\w*|IN|INPUT|VBUS\w*|VDC|DC_?IN|VBAT\w*|VSUP\w*|PVIN|\+?(20|24|36|48)V\w*)([^A-Z]|$)")
OUT_RE = re.compile(r"(^|[^A-Z])(V_?OUT\w*|OUT|OUTPUT|LOAD|VO|\+?12V(_?OUT)?)([^A-Z0-9]|$)")
SW_PIN_RE = re.compile(r"^(P?SW\d*|LX\d*|PH|VSW|PHASE)$", re.I)
IC_POWER_PIN_RE = re.compile(r"^(P?VIN\d*|VCC_?IN|P?GND\d*|EP|PAD|P?SW\d*|LX\d*|PH|VSW)$", re.I)
FB_PIN_RE = re.compile(r"^(V?FB\d*|FBK|VSENSE|VOSNS|FB[+-]|INV|VFB)$", re.I)
SUPPLY_PIN_RE = re.compile(r"^(VCC\w*|VDD\w*|AVDD|DVDD|V\+|VS|VIN|VBIAS|VREG|BIAS|VDRV|PVCC|AVCC|VCCA|VDDA|LDO\w*)$", re.I)


class GateLink:
    def __init__(self, fet, gate_pad, driver=None, driver_pad=None, resistor=None, nets=()):
        self.fet = fet
        self.gate_pad = gate_pad
        self.driver = driver
        self.driver_pad = driver_pad
        self.resistor = resistor
        self.nets = list(nets)


class Analysis:
    def __init__(self, board, overrides=None, overload=False):
        self.b = board
        self.overrides = overrides or {}
        self.overload = overload
        self.net_pads = defaultdict(list)
        for f in board.footprints:
            for p in f.pads:
                if p.net and p.layers:
                    self.net_pads[p.net].append(p)
        self._classify_parts()
        self._classify_nets()
        self._trace_control()

    # -- parts -------------------------------------------------------------
    def _classify_parts(self):
        b = self.b
        self.mosfets, self.fet_roles = [], {}
        self.magnetics, self.transformers = [], []
        self.diodes, self.power_diodes, self.tvs = [], [], []
        self.shunts, self.fuses, self.links = [], [], []
        self.connectors, self.test_points, self.mount_holes, self.fiducials = [], [], [], []
        self.ics, self.caps, self.resistors, self.leds, self.crystals = [], [], [], [], []
        self.cap_value = {}

        for f in b.footprints:
            if "dnp" in f.attrs:
                continue
            px = f.prefix
            blob = f.text_blob()
            pads = f.copper_pads()
            maxpad = max((p.area for p in pads), default=0)
            if px.startswith("TP") or "testpoint" in blob or "test_point" in blob:
                self.test_points.append(f)
            elif px in ("H", "MH", "HOLE") or "mountinghole" in blob or "mounting_hole" in blob:
                self.mount_holes.append(f)
            elif px.startswith("FID") or "fiducial" in blob:
                self.fiducials.append(f)
            elif px in ("Y", "XTAL") or re.search(r"crystal|xtal|oscillator|resonator", blob):
                self.crystals.append(f)
            elif px in ("J", "P", "CN", "CON", "X", "XT", "K", "BAN") or \
                    re.search(r"conn|terminal|header|banana|jack|xt30|xt60|phoenix|screw|socket|pinhead|wire_pad|solderwire", blob):
                self.connectors.append(f)
            elif px in ("Q", "M", "FET", "T") and len(pads) >= 3 and not re.search(r"transformer|trafo", blob):
                if maxpad >= 1.0 or re.search(r"to-?220|to-?247|to-?252|to-?263|d2?pak|powerpak|pqfn|lfpak|toll|hsof|tdson|superso|vson|dfn|so-?8|soic-?8|power", blob):
                    self.mosfets.append(f)
                    self.fet_roles[f.ref] = self._fet_roles(f)
            elif px in ("L", "T", "TR", "TX") or re.search(r"inductor|transformer|choke|coupled", blob):
                if re.search(r"bead|ferrite", blob) or px == "FB":
                    self.links.append(f)
                elif len(pads) >= 2 and (maxpad >= 1.0 or f.body_area >= 16):
                    self.magnetics.append(f)
                    if px in ("T", "TR", "TX") or re.search(r"transformer|coupled|trafo", blob):
                        self.transformers.append(f)
            elif px == "FB":
                self.links.append(f)
            elif px in ("D", "LED", "TVS", "Z", "ZD", "CR", "V"):
                if px == "LED" or re.search(r"\bled\b|led_|_led", blob):
                    self.leds.append(f)
                elif re.search(r"tvs|smbj|smaj|smcj|p6ke|1\.5ke|sm6t|esd|transil", blob) or px == "TVS":
                    self.tvs.append(f)
                else:
                    self.diodes.append(f)
            elif px in ("F", "PTC") or re.search(r"\bfuse|polyfuse|ptc", blob):
                self.fuses.append(f)
            elif px in ("U", "IC", "IC_") and len(pads) >= 3:
                self.ics.append(f)
            elif px == "C" and len(pads) >= 2:
                self.caps.append(f)
                self.cap_value[f.ref] = cap_farads(f.value)
            elif px in ("R", "RS", "RSH", "SHUNT"):
                self.resistors.append(f)
                ohm = res_ohms(f.value)
                if ohm is not None and ohm == 0:
                    self.links.append(f)
                elif ohm is not None and ohm < 1.0 or px in ("RS", "RSH", "SHUNT"):
                    self.shunts.append(f)

        # small inductors belong to auxiliary supplies, not to the 60 W power stage
        self.aux_magnetics = []
        if self.magnetics:
            size = {f.ref: max(f.body_area, max((p.area for p in f.copper_pads()), default=0) * 4) for f in self.magnetics}
            biggest = max(size.values())
            self.aux_magnetics = [f for f in self.magnetics if size[f.ref] < 0.3 * biggest and f not in self.transformers]
            self.magnetics = [f for f in self.magnetics if f not in self.aux_magnetics]

    def _fet_roles(self, f):
        roles = {}
        pads = f.copper_pads()
        for p in pads:
            pf = (p.pinfunction or "").upper().strip()
            if re.fullmatch(r"G(ATE)?\d*", pf):
                roles[id(p)] = "G"
            elif re.fullmatch(r"D(RAIN)?\d*|TAB", pf):
                roles[id(p)] = "D"
            elif re.fullmatch(r"(K|KELVIN_?)?S(OURCE)?\d*|SS|KS", pf):
                roles[id(p)] = "S"
        if not any(r == "G" for r in roles.values()):
            roles = self._fet_roles_by_wiring(f, pads)
        if not any(r == "G" for r in roles.values()):
            roles = {}
            lib = f.lib.lower()
            nums = {p.number for p in pads}

            def by(mapping, default):
                for p in pads:
                    roles[id(p)] = mapping.get(p.number, default)

            if re.search(r"to-?220|to-?247|to-?3p|to-?262|to-?251|ipak", lib):
                by({"1": "G", "2": "D", "3": "S"}, "D")
            elif re.search(r"to-?263-7|d2pak-7", lib):
                by({"1": "G", "4": "D"}, "S")
            elif re.search(r"to-?252|dpak|to-?263|d2pak", lib):
                by({"1": "G", "3": "S"}, "D")
            elif re.search(r"sot-?23|sc-?70|sot-?323", lib):
                by({"1": "G", "2": "S", "3": "D"}, "D")
            elif re.search(r"toll|hsof", lib):
                by({"1": "G"}, "S")
                for p in pads:
                    if p.area == max(q.area for q in pads):
                        roles[id(p)] = "D"
            elif re.search(r"so-?8|soic-?8|powerpak|pqfn|dfn|vson|tdson|son|superso|lfpak|qfn", lib) or \
                    {"1", "2", "3", "4", "5"} <= nums:
                by({"1": "S", "2": "S", "3": "S", "4": "G"}, "D")
        # pads that share a net with a known role take that role
        net_role = {}
        for p in pads:
            r = roles.get(id(p))
            if r and p.net:
                net_role.setdefault(p.net, r)
        for p in pads:
            if id(p) not in roles:
                roles[id(p)] = net_role.get(p.net, "P")
        return roles

    def _fet_roles_by_wiring(self, f, pads):
        """Gate = the one small pin whose net goes to a resistor or IC; drain = the
        net with the most pad area (the tab); source = the rest."""
        by_net = defaultdict(list)
        for p in pads:
            if p.net:
                by_net[p.net].append(p)
        if len(by_net) < 3:
            return {}
        min_area = min(p.area for p in pads)
        gate_nets = []
        for net, ps in by_net.items():
            if len(ps) != 1 or ps[0].area > min_area * 1.6 or GND_RE.search(base_name(net)):
                continue
            others = [q for q in self.net_pads.get(net, []) if q.fp is not f]
            if 0 < len(others) <= 6 and any(q.fp.prefix in ("R", "U", "IC", "D") for q in others):
                gate_nets.append(net)
        if len(gate_nets) != 1:
            return {}
        rest = {n: sum(p.area for p in ps) for n, ps in by_net.items() if n != gate_nets[0]}
        ranked = sorted(rest.items(), key=lambda kv: -kv[1])
        roles = {id(by_net[gate_nets[0]][0]): "G"}
        if len(ranked) >= 2 and ranked[0][1] > ranked[1][1] * 1.3:
            for n, _ in ranked:
                for p in by_net[n]:
                    roles[id(p)] = "D" if n == ranked[0][0] else "S"
            return roles
        # equal pads (TO-220 style): take drain/source from the usual pinout
        lib = f.lib.lower()
        pin_d = "2" if re.search(r"to-?2[2-6]|to-?247|ipak|dpak|d2pak|to-?3p", lib) else None
        for n, _ in ranked:
            for p in by_net[n]:
                roles[id(p)] = "D" if pin_d and p.number == pin_d else ("S" if pin_d else "P")
        return roles

    def fet_pads(self, f, role):
        roles = self.fet_roles.get(f.ref, {})
        return [p for p in f.copper_pads() if roles.get(id(p)) == role]

    def fet_power_pads(self, f):
        roles = self.fet_roles.get(f.ref, {})
        return [p for p in f.copper_pads() if roles.get(id(p)) != "G"]

    # -- nets ----------------------------------------------------------------
    def _classify_nets(self):
        b = self.b
        ov = self.overrides
        nets = set(self.net_pads)
        self.gnd = {n for n in nets if GND_RE.search(base_name(n))}
        if ov.get("gnd"):
            self.gnd = set(ov["gnd"]) & nets or self.gnd
        if not self.gnd and nets:
            self.gnd = {max(nets, key=lambda n: len(self.net_pads[n]))}

        mag_nets = {p.net for f in self.magnetics for p in f.copper_pads() if p.net}
        fet_nets = {p.net for f in self.mosfets for p in self.fet_power_pads(f) if p.net}

        # integrated-switch ICs: an IC pin on a magnetic's net that is a switch pin
        self.switch_ics = []
        ic_switch_nets = set()
        for f in self.ics:
            # an IC "SW" pin on a net that already has power MOSFETs is a driver's reference pin,
            # not an integrated switch
            on_mag = [p for p in f.copper_pads() if p.net in mag_nets and p.net not in self.gnd and p.net not in fet_nets]
            sw = [p for p in on_mag if SW_PIN_RE.match(p.pinfunction or "")]
            if sw:
                self.switch_ics.append(f)
                ic_switch_nets |= {p.net for p in sw}

        seed = mag_nets | fet_nets | ic_switch_nets
        for f in self.diodes:
            pads = f.copper_pads()
            if any(p.net in seed and p.net not in self.gnd for p in pads) and max((p.area for p in pads), default=0) >= 0.8:
                self.power_diodes.append(f)
        diode_nets = {p.net for f in self.power_diodes for p in f.copper_pads() if p.net}
        # a freewheeling diode goes from the switch node to ground (or, on a transformer, rectifies a winding)
        freewheel_nets = set()
        xfmr_nets = {p.net for f in self.transformers for p in f.copper_pads() if p.net}
        for f in self.power_diodes:
            pn = {p.net for p in f.copper_pads() if p.net}
            if pn & self.gnd or pn & xfmr_nets:
                freewheel_nets |= pn - self.gnd

        self.sw = set()
        for n in mag_nets:
            if n in self.gnd:
                continue
            if n in fet_nets or n in freewheel_nets or n in ic_switch_nets:
                self.sw.add(n)
        # an inductor always has a switch on one side: if none was found, take the inductor
        # net with a switch-node name, else the one that reaches an IC with fewer connections
        sw_name = re.compile(r"(^|[^A-Z])(SW|LX|PH|PHASE|SWNODE|SW_NODE|VSW)(\d*)([^A-Z]|$)")
        for f in self.magnetics:
            if f in self.transformers:
                continue
            own = {p.net for p in f.copper_pads() if p.net and p.net not in self.gnd}
            if own & self.sw:
                continue
            named = [n for n in own if sw_name.search(base_name(n))]
            # a switch node never has a capacitor straight to ground (filter chokes have one on both sides)
            cand = named or [n for n in own if n not in fet_nets and not self._cap_to_gnd(n)
                             and any(q.fp in self.ics for q in self.net_pads[n])]
            if cand:
                n = min(cand, key=lambda n: len(self.net_pads[n]))
                self.sw.add(n)
                for q in self.net_pads[n]:
                    if q.fp in self.ics and q.fp not in self.switch_ics:
                        self.switch_ics.append(q.fp)
                seed.add(n)
        if ov.get("sw"):
            self.sw = set(ov["sw"]) & nets or self.sw

        hc = set(seed | diode_nets)
        for f in self.switch_ics:
            for p in f.copper_pads():
                if p.net and IC_POWER_PIN_RE.match(p.pinfunction or ""):
                    hc.add(p.net)
        conn_nets = {p.net for f in self.connectors for p in f.copper_pads() if p.net}
        for _ in range(4):
            grown = False
            for f in self.shunts + self.fuses + self.links:
                pn = {p.net for p in f.copper_pads() if p.net}
                if pn & (hc - self.gnd) or (f in self.fuses and pn & conn_nets):
                    if f in self.links and not (pn & (hc - self.gnd)):
                        continue
                    if not pn <= hc:
                        hc |= pn
                        grown = True
            if not grown:
                break
        hc.discard("")
        self.hc = hc
        self.power_connectors = [f for f in self.connectors
                                 if any(p.net in hc and p.net not in self.gnd for p in f.copper_pads())]

        # input / output side
        self.input, self.output = set(), set()
        for n in hc - self.gnd - self.sw:
            bn = base_name(n)
            if IN_RE.search(bn):
                self.input.add(n)
            elif OUT_RE.search(bn):
                self.output.add(n)
        pconn_nets = {p.net for f in self.power_connectors for p in f.copper_pads() if p.net}
        for n in hc - self.gnd - self.sw - self.input - self.output:
            pads = self.net_pads[n]
            parts = {p.fp for p in pads}
            if any(f in self.transformers for f in parts):
                self.input.add(n)
                continue
            if any(f in self.switch_ics and IC_POWER_PIN_RE.match(p.pinfunction or "") and "IN" in (p.pinfunction or "").upper()
                   for p in pads for f in [p.fp]):
                self.input.add(n)
                continue
            hs_drain = False
            for p in pads:
                if p.fp in self.mosfets and self.fet_roles[p.fp.ref].get(id(p)) == "D":
                    if any(q.net in self.sw for q in self.fet_pads(p.fp, "S")):
                        hs_drain = True
            if hs_drain:
                self.input.add(n)
            elif any(f in self.magnetics for f in parts) and n in pconn_nets | self._cap_nets():
                self.output.add(n)
            elif any(f in self.power_diodes for f in parts) and n in pconn_nets and not self.transformers == []:
                self.output.add(n)
        # carry the side across series parts (fuse, shunt, reverse-polarity FET/diode, bead)
        series = self.fuses + self.shunts + self.links + [f for f in self.mosfets] + self.power_diodes
        for _ in range(4):
            changed = False
            for f in series:
                pads = self.fet_power_pads(f) if f in self.mosfets else f.copper_pads()
                pn = {p.net for p in pads if p.net} & hc - self.gnd - self.sw
                if len(pn) != 2:
                    continue
                for side in (self.input, self.output):
                    if pn & side and not pn <= side and not pn & (self.output if side is self.input else self.input):
                        side |= pn
                        changed = True
            if not changed:
                break
        if ov.get("input"):
            self.input = set(ov["input"]) & nets or self.input
        if ov.get("output"):
            self.output = set(ov["output"]) & nets or self.output
        self.output -= self.input

        p_out = PROJECT["vout"] * (PROJECT["iout_overload"] if self.overload else PROJECT["iout_rated"])
        self.i_out = PROJECT["iout_overload"] if self.overload else PROJECT["iout_rated"]
        self.i_in = p_out / (PROJECT["efficiency_guess"] * PROJECT["vin_min"])
        self.net_current = {}
        self.net_voltage = {}
        for n in hc:
            if n in self.input:
                self.net_current[n] = self.i_in
                self.net_voltage[n] = PROJECT["vin_max"]
            elif n in self.output:
                self.net_current[n] = self.i_out
                self.net_voltage[n] = PROJECT["vout"]
            elif n in self.gnd:
                self.net_current[n] = max(self.i_out, self.i_in)
                self.net_voltage[n] = 0.0
            elif n in self.sw:
                self.net_current[n] = max(self.i_out, self.i_in)
                self.net_voltage[n] = PROJECT["vin_max"] * PROJECT["v_peak_margin"]
            else:
                self.net_current[n] = max(self.i_out, self.i_in)
                self.net_voltage[n] = PROJECT["vin_max"]

        # power-path pads (the ends the load current flows between) for each net
        self.terminals = defaultdict(list)
        for f in self.mosfets:
            for p in self.fet_power_pads(f):
                self.terminals[p.net].append(p)
        for f in self.power_diodes + self.magnetics + self.shunts + self.fuses:
            for p in f.copper_pads():
                self.terminals[p.net].append(p)
        for f in self.switch_ics:
            for p in f.copper_pads():
                if IC_POWER_PIN_RE.match(p.pinfunction or "") or p.net in self.sw:
                    self.terminals[p.net].append(p)
        for f in self.power_connectors:
            for p in f.copper_pads():
                if p.net in hc:
                    self.terminals[p.net].append(p)
        # capacitors are not terminals: they carry ripple, not the load current
        self.terminals = {n: v for n, v in self.terminals.items() if n in hc}

    def _cap_to_gnd(self, net):
        for p in self.net_pads.get(net, []):
            if p.fp in self.caps and any(q.net in self.gnd for q in p.fp.copper_pads() if q is not p):
                return True
        return False

    def _cap_nets(self):
        return {p.net for f in self.caps for p in f.copper_pads() if p.net}

    @staticmethod
    def is_polarized(f):
        blob = f.text_blob()
        return bool(re.search(r"cp_|c_?pol|elec|polarized|tantal|radial|aluminum|alu|_cp|capacitor_?tht.*cp", blob))

    def is_ceramic(self, f):
        val = self.cap_value.get(f.ref)
        return not self.is_polarized(f) and (val is None or val <= 47e-6)

    # -- control side ----------------------------------------------------------
    def _trace_control(self):
        ic_set = set(self.ics)
        self.gates = []
        for f in self.mosfets:
            for gp in self.fet_pads(f, "G"):
                if not gp.net:
                    continue
                link = GateLink(f, gp, nets=[gp.net])
                direct = [p for p in self.net_pads[gp.net] if p.fp in ic_set]
                if direct:
                    link.driver, link.driver_pad = direct[0].fp, direct[0]
                else:
                    for p in self.net_pads[gp.net]:
                        r = p.fp
                        if r in self.resistors and r not in self.shunts:
                            # a gate resistor leads to a driver output, never to ground or a power rail
                            other = [q for q in r.copper_pads() if q.net and q.net != gp.net
                                     and q.net not in self.gnd and q.net not in self.hc]
                            for q in other:
                                ic_p = [x for x in self.net_pads[q.net] if x.fp in ic_set]
                                if ic_p:
                                    link.driver, link.driver_pad, link.resistor = ic_p[0].fp, ic_p[0], r
                                    link.nets.append(q.net)
                                    break
                        if link.driver:
                            break
                self.gates.append(link)
        self.drivers = []
        for g in self.gates:
            if g.driver and g.driver not in self.drivers:
                self.drivers.append(g.driver)

        self.bootstrap = []
        for f in self.caps:
            pads = f.copper_pads()
            if len(pads) != 2:
                continue
            a, c = pads
            for p, q in ((a, c), (c, a)):
                if p.net in self.sw and q.net and q.net not in self.hc and q.net not in self.gnd:
                    ic_p = [x for x in self.net_pads[q.net] if x.fp in ic_set]
                    if ic_p:
                        self.bootstrap.append((f, q, ic_p[0]))
        self.feedback = []
        for f in self.ics:
            for p in f.copper_pads():
                if p.net and FB_PIN_RE.match(p.pinfunction or ""):
                    rs = [x.fp for x in self.net_pads[p.net] if x.fp in self.resistors]
                    self.feedback.append((p, rs))
        self.controllers = [f for f in self.ics if f in self.drivers or f in self.switch_ics or
                            any(fb[0].fp is f for fb in self.feedback)]

        self.input_caps, self.output_caps = [], []
        for f in self.caps:
            nets_ = {p.net for p in f.copper_pads()}
            if nets_ & self.gnd and nets_ & self.input:
                self.input_caps.append(f)
            elif nets_ & self.gnd and nets_ & self.output:
                self.output_caps.append(f)

    # -- summary --------------------------------------------------------------
    def topology(self):
        if self.transformers:
            return "isolated converter (transformer found: " + ", ".join(f.ref for f in self.transformers) + ")"
        inductors = [f for f in self.magnetics if f not in self.transformers]
        if not inductors:
            return "unknown (no power inductor or transformer found)"
        if self.switch_ics and not self.mosfets:
            return f"buck converter with integrated switch ({', '.join(f.ref for f in self.switch_ics)})"
        if len(self.sw) >= 2 and len(inductors) == 1:
            return "4-switch buck-boost (two switch nodes on one inductor)"
        if len(inductors) >= 2:
            return "multi-inductor converter (SEPIC, Cuk, interleaved or with an output filter)"
        sw_fets = [f for f in self.mosfets if any(p.net in self.sw for p in self.fet_power_pads(f))]
        sw_diodes = [f for f in self.power_diodes if any(p.net in self.sw for p in f.copper_pads())]
        if self.sw and self.output:
            if len(sw_fets) >= 2:
                return "synchronous buck (two switches on the switch node)"
            if sw_fets and sw_diodes:
                return "non-synchronous buck (switch + diode)"
            return "buck-type converter"
        return "not sure (check the net roles below)"

    def summary(self):
        def refs(lst):
            return ", ".join(sorted((f.ref for f in lst), key=_natural)) or "none found"

        def nets(s):
            return ", ".join(sorted(s)) or "none found"

        lines_parts = [
            f"Topology guess: {self.topology()}",
            f"Power switches (MOSFETs): {refs(self.mosfets)}",
            f"Power diodes: {refs(self.power_diodes)}",
            f"Inductors / transformers: {refs(self.magnetics)}"
            + (f"   (small ones, taken as auxiliary supplies: {refs(self.aux_magnetics)})" if self.aux_magnetics else ""),
            f"Controller / driver ICs: {refs(self.controllers)}",
            f"Power connectors: {refs(self.power_connectors)}",
            f"Input capacitors: {refs(self.input_caps)}",
            f"Output capacitors: {refs(self.output_caps)}",
            f"Current-sense shunts: {refs(self.shunts)}",
            f"Fuses: {refs(self.fuses)}   TVS: {refs(self.tvs)}",
            f"Test points: {refs(self.test_points)}",
        ]
        lines_nets = [
            f"Input side (up to {PROJECT['vin_max']:g} V, ~{self.i_in:.1f} A): {nets(self.input)}",
            f"Switch node(s) (up to ~{PROJECT['vin_max'] * PROJECT['v_peak_margin']:.0f} V peak): {nets(self.sw)}",
            f"Output side ({PROJECT['vout']:g} V, {self.i_out:g} A): {nets(self.output)}",
            f"Ground: {nets(self.gnd)}",
            "Other high-current nets (checked as up to "
            f"{PROJECT['vin_max']:g} V, {max(self.i_in, self.i_out):g} A): {nets(self.hc - self.input - self.output - self.sw - self.gnd)}",
        ]
        lines_ctrl = []
        for g in self.gates:
            via = f" through {g.resistor.ref}" if g.resistor else ""
            drv = f"{g.driver.ref} pin {g.driver_pad.number}{via}" if g.driver else "no driver IC found"
            lines_ctrl.append(f"{g.fet.ref} gate ({g.gate_pad.net}) <- {drv}")
        for c, q, icp in self.bootstrap:
            lines_ctrl.append(f"Bootstrap capacitor {c.ref} ({fmt_cap(self.cap_value.get(c.ref))}) -> {icp.fp.ref} pin {icp.number}")
        for p, rs in self.feedback:
            lines_ctrl.append(f"Feedback: {p.fp.ref} pin {p.number} ({p.pinfunction}) with {', '.join(r.ref for r in rs) or 'no resistor'}")
        return [("Parts", lines_parts), ("Nets", lines_nets), ("Gate drive and control", lines_ctrl or ["nothing found"])]


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]
