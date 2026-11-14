"""Findings and the report object the checks fill in."""

SEVERITIES = ("error", "warning", "info")
SEVERITY_TEXT = {
    "error": "Must fix",
    "warning": "Should fix",
    "info": "Check",
}

CATEGORIES = [
    ("submission", "Submission files"),
    ("fab", "Manufacturing (PCBWay)"),
    ("power", "Power stage (EE463)"),
    ("layout", "Layout"),
    ("test", "Testing and assembly"),
    ("drc", "KiCad DRC"),
]


class Finding:
    def __init__(self, check, severity, title, message, locations=None, refs=None, fix="", rule=""):
        self.check = check
        self.severity = severity
        self.title = title
        self.message = message
        self.locations = locations or []   # (x, y, layer, label)
        self.refs = refs or []
        self.fix = fix
        self.rule = rule
        self.waived = ""

    def to_dict(self):
        return {
            "check": self.check, "severity": self.severity, "title": self.title,
            "message": self.message, "fix": self.fix, "rule": self.rule,
            "refs": self.refs, "waived": self.waived,
            "locations": [{"x": round(x, 3), "y": round(y, 3), "layer": l, "label": lab}
                          for x, y, l, lab in self.locations],
        }


class Check:
    def __init__(self, cid, category, title, rule=""):
        self.id = cid
        self.category = category
        self.title = title
        self.rule = rule
        self.findings = []
        self.skipped = ""

    @property
    def status(self):
        if self.skipped:
            return "skipped"
        active = [f for f in self.findings if not f.waived]
        for sev in SEVERITIES:
            if any(f.severity == sev for f in active):
                return sev
        return "pass"


class Report:
    def __init__(self):
        self.title = "EE463 PCB Check"
        self.board_name = ""
        self.source = ""
        self.files = []
        self.meta = {}          # key facts shown at the top
        self.detected = []      # (heading, [lines]) shown under "What the checker found"
        self.checks = {}        # id -> Check
        self.order = []
        self.notes = []
        self.manual = []
        self.drawing = None     # board drawing for the SVG view
        self.settings = {}

    def check(self, cid, category, title, rule=""):
        if cid not in self.checks:
            self.checks[cid] = Check(cid, category, title, rule)
            self.order.append(cid)
        return self.checks[cid]

    def add(self, cid, severity, message, locations=None, refs=None, fix="", title=None):
        c = self.checks[cid]
        f = Finding(cid, severity, title or c.title, message, locations, refs, fix, c.rule)
        c.findings.append(f)
        return f

    def skip(self, cid, reason):
        self.checks[cid].skipped = reason

    def findings(self, include_waived=False):
        for cid in self.order:
            for f in self.checks[cid].findings:
                if include_waived or not f.waived:
                    yield f

    def counts(self):
        c = {s: 0 for s in SEVERITIES}
        for f in self.findings():
            c[f.severity] += 1
        return c

    def apply_waivers(self, waivers, ignore):
        for cid in ignore or []:
            if cid in self.checks:
                for f in self.checks[cid].findings:
                    f.waived = "Ignored in pcb_checker.json"
        for w in waivers or []:
            cid = w.get("check")
            ref = w.get("ref")
            reason = w.get("reason", "waived")
            for f in self.checks.get(cid, Check("", "", "")).findings:
                if not ref or ref in f.refs or ref in f.message:
                    f.waived = reason

    def verdict(self):
        c = self.counts()
        if c["error"]:
            return "fail", f"Not ready: {c['error']} problem(s) must be fixed before you send the files."
        if c["warning"]:
            return "warn", f"Almost: fix or explain {c['warning']} warning(s) before you send the files."
        return "pass", "No problems found by the automatic checks. Do the manual checks below before sending."

    def to_dict(self):
        return {
            "title": self.title, "board": self.board_name, "source": self.source,
            "meta": self.meta, "settings": self.settings,
            "verdict": self.verdict()[1], "counts": self.counts(),
            "detected": [{"heading": h, "lines": l} for h, l in self.detected],
            "checks": [{"id": c.id, "category": c.category, "title": c.title, "status": c.status,
                        "skipped": c.skipped, "findings": [f.to_dict() for f in c.findings]}
                       for c in (self.checks[i] for i in self.order)],
            "notes": self.notes,
        }
