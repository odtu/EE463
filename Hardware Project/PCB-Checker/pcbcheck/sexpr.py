"""Minimal S-expression reader for KiCad files (.kicad_pcb).

A node is a Python list whose first element is its name, e.g.
["segment", ["start", "1", "2"], ["end", "3", "4"], ["width", "0.2"], ...].
Atoms stay strings; callers convert numbers where they need them.
"""

import re

_TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def _unquote(tok):
    s = tok[1:-1]
    if "\\" in s:
        s = (s.replace('\\"', '"').replace("\\n", "\n")
              .replace("\\t", "\t").replace("\\\\", "\\"))
    return s


def parse(text):
    """Parse the first S-expression in text and return it as nested lists."""
    stack = []
    root = None
    for m in _TOKEN.finditer(text):
        tok = m.group(0)
        if tok == "(":
            node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif tok == ")":
            if not stack:
                raise ValueError("Unbalanced ')' in file")
            node = stack.pop()
            if not stack:
                root = node
                break
        elif stack:
            stack[-1].append(_unquote(tok) if tok[0] == '"' else tok)
    if root is None:
        raise ValueError("No S-expression found (is this a KiCad file?)")
    return root


def find(node, name):
    """First child list called name, or None."""
    for child in node[1:]:
        if isinstance(child, list) and child and child[0] == name:
            return child
    return None


def findall(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def atoms(node):
    """The plain (non-list) arguments of a node, without its name."""
    return [c for c in node[1:] if not isinstance(c, list)]


def value(node, name, default=None, index=0):
    """Atom number `index` of child `name`, as a string."""
    child = find(node, name)
    if child is None:
        return default
    a = atoms(child)
    return a[index] if len(a) > index else default


def num(node, name, default=None, index=0):
    v = value(node, name, None, index)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def xy(node, name):
    """(x, y) of a child like (start 1 2); None if missing."""
    child = find(node, name)
    if child is None:
        return None
    a = atoms(child)
    try:
        return float(a[0]), float(a[1])
    except (IndexError, ValueError):
        return None


def flag(node, name):
    """True for (name yes), a bare `name` atom, or (name) with no args."""
    for c in node[1:]:
        if c == name:
            return True
        if isinstance(c, list) and c and c[0] == name:
            a = atoms(c)
            return not a or a[0] not in ("no", "false")
    return False
