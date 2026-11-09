"""Tiny schematic writer: places stock-library symbols and connects pins with
short wire stubs + net labels / power symbols. Produces a KiCad .kicad_sch."""
import copy
import uuid as _uuid

from kilib import get_symbol, pins
from sexp import Sym, dump, find, find_all

S = Sym
GRID = 1.27
STUB = 2.54

POWER_NETS = {"GND", "+3V3", "+5V", "+24V", "VBUS"}
# body direction of the power symbol in its natural orientation
POWER_BODY = {"GND": "down"}
ROT_FOR = {  # (natural body dir, desired outward dir) -> rotation
    ("down", "down"): 0, ("down", "right"): 90, ("down", "up"): 180, ("down", "left"): 270,
    ("up", "up"): 0, ("up", "left"): 90, ("up", "down"): 180, ("up", "right"): 270,
}


_NS = _uuid.UUID("6b1e2c4a-6f0b-4f8e-9a51-7a3e0c2d9b10")
_counter = [0]


def uid(key=None):
    """Deterministic UUIDs so regenerating the schematic keeps the PCB links."""
    if key is None:
        _counter[0] += 1
        key = "item:%d" % _counter[0]
    return str(_uuid.uuid5(_NS, key))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def _font(size=1.27, bold=False):
    f = [S("font"), [S("size"), size, size]]
    if bold:
        f.append([S("bold"), S("yes")])
    return f


DIRS = {0: "right", 90: "up", 180: "left", 270: "down"}
STEP = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}


class Part:
    """A placed symbol: absolute pin coordinates and outward pin directions (rotation applied)."""

    def __init__(self, sch, ref, sym, x, y, rot):
        self.sch, self.ref, self.x, self.y, self.rot = sch, ref, x, y, rot
        self._pins = {}
        for p in pins(sym):
            px, py = p["x"], p["y"]
            r = rot % 360
            rx, ry = {0: (px, py), 90: (-py, px), 180: (-px, -py), 270: (py, -px)}[r]
            out = DIRS[int(p["angle"] + 180 + r) % 360]
            self._pins.setdefault(p["number"], (snap(x + rx), snap(y - ry), out))

    def __getitem__(self, num):
        """(x, y) of a pin."""
        px, py, _ = self._pins[str(num)]
        return (px, py)

    def out(self, num):
        return self._pins[str(num)][2]

    def end(self, num, length=STUB):
        """Point `length` mm outward from a pin."""
        px, py, d = self._pins[str(num)]
        dx, dy = STEP[d]
        return (snap(px + dx * length), snap(py + dy * length))

    def stub(self, num, net, length=STUB):
        """Short wire out of a pin ending in a power symbol (power nets) or a net label."""
        px, py = self[num]
        ex, ey = self.end(num, length)
        self.sch.w((px, py), (ex, ey))
        if net in POWER_NETS:
            self.sch.power(net, ex, ey, self.out(num))
        else:
            self.sch.label(net, ex, ey, self.out(num))
        return (ex, ey)

    def nc(self, *nums):
        for n in nums:
            self.sch.no_connect(*self[n])


class Schematic:
    def __init__(self, project, title, rev="", comments=()):
        self.project = project
        self.root = uid("root:" + project)
        self.title = title
        self.rev = rev
        self.comments = comments
        self.libs = {}
        self.items = []
        self.pwr_n = 0
        self.refs = set()
        self.net_pins = {}

    # ---------------------------------------------------------------- symbols
    def _lib(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = get_symbol(lib_id)
        return self.libs[lib_id]

    def _instance(self, lib_id, ref, value, x, y, rot=0, footprint=None, props=None,
                  in_bom=True, dnp=False, hide_ref=False, hide_val=False, fields=None):
        sym = self._lib(lib_id)
        hook = getattr(self, "prop_hook", None)
        if hook and in_bom:
            props = dict(props or {})
            props.update(hook(ref, lib_id, value, footprint))
        node = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, rot], [S("unit"), 1],
                [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes" if in_bom else "no")],
                [S("on_board"), S("yes")], [S("dnp"), S("yes" if dnp else "no")],
                [S("uuid"), uid("sym:" + ref)]]
        lib_props = {p[1]: p for p in find_all(sym, "property")}

        def prop(name, val, dx, dy, hide, angle=0, effects=None):
            node_p = [S("property"), name, val, [S("at"), snap(x + dx), snap(y + dy), angle]]
            if hide:
                node_p.append([S("hide"), S("yes")])
            node_p.append(effects or [S("effects"), _font()])
            node.append(node_p)

        def lib_field(name, val, hide):
            if fields and name in fields:     # explicit position, horizontal centred text
                dx, dy = fields[name]
                prop(name, val, dx, dy, hide, (0 - rot) % 180, [S("effects"), _font()])
                return
            lp = lib_props[name]
            at = find(lp, "at")
            dx, dy = float(at[1]), -float(at[2])
            ang = float(at[3]) if len(at) > 3 else 0
            c, s_ = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot % 360]
            dx, dy = dx * c + dy * s_, -dx * s_ + dy * c
            eff = copy.deepcopy(find(lp, "effects")) or [S("effects"), _font()]
            eff = [e for e in eff if not (isinstance(e, list) and e[0] == "hide")]
            if rot % 180:
                ang = (ang + 90) % 180
            prop(name, val, dx, dy, hide, ang, eff)

        lib_field("Reference", ref, hide_ref)
        lib_field("Value", value, hide_val)
        fp = footprint
        if fp is None:
            for p in find_all(sym, "property"):
                if p[1] == "Footprint":
                    fp = p[2]
        prop("Footprint", fp or "", 0, 0, True)
        prop("Datasheet", "~", 0, 0, True)
        for k, v in (props or {}).items():
            prop(k, v, 0, 0, True)
        for p in pins(sym):
            node.append([S("pin"), p["number"], [S("uuid"), uid("pin:%s:%s" % (ref, p["number"]))]])
        node.append([S("instances"), [S("project"), self.project,
                     [S("path"), "/" + self.root, [S("reference"), ref], [S("unit"), 1]]]])
        self.items.append(node)
        return sym

    # ---------------------------------------------------------------- drawing
    def wire(self, x1, y1, x2, y2):
        if (x1, y1) == (x2, y2):
            return
        self.items.append([S("wire"), [S("pts"), [S("xy"), x1, y1], [S("xy"), x2, y2]],
                           [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid()]])

    def w(self, *pts):
        """Polyline through points [(x, y), ...]; every vertex is a wire end (safe connections)."""
        pts = [(snap(x), snap(y)) for x, y in pts]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            assert x1 == x2 or y1 == y2, "non-orthogonal wire %s -> %s" % ((x1, y1), (x2, y2))
            self.wire(x1, y1, x2, y2)

    def junction(self, x, y):
        self.items.append([S("junction"), [S("at"), snap(x), snap(y)], [S("diameter"), 0],
                           [S("color"), 0, 0, 0, 0], [S("uuid"), uid()]])

    def label(self, net, x, y, direction, size=1.27):
        x, y = snap(x), snap(y)
        angle = {"right": 0, "up": 90, "left": 180, "down": 270}[direction]
        just = "left" if direction in ("right", "up") else "right"
        self.items.append([S("label"), net, [S("at"), x, y, angle],
                           [S("effects"), _font(size), [S("justify"), S(just), S("bottom")]], [S("uuid"), uid()]])

    def power(self, net, x, y, direction=None):
        if direction is None:
            direction = "down" if net == "GND" else "up"
        x, y = snap(x), snap(y)
        self.pwr_n += 1
        body = POWER_BODY.get(net, "up")
        rot = ROT_FOR[(body, direction)]
        self._instance("power:" + net, "#PWR%03d" % self.pwr_n, net, x, y, rot,
                       footprint="", in_bom=False, hide_ref=True)

    def pwr_flag(self, net, x, y):
        self.pwr_n += 1
        self._instance("power:PWR_FLAG", "#FLG%03d" % self.pwr_n, "PWR_FLAG", x, y, 0,
                       footprint="", in_bom=False, hide_ref=True, hide_val=True)
        if net in POWER_NETS:
            self.power(net, x, y, "down" if net == "GND" else "up")
        else:
            self.wire(x, y, x, y + STUB)
            self.label(net, x, y + STUB, "down")

    def no_connect(self, x, y):
        self.items.append([S("no_connect"), [S("at"), x, y], [S("uuid"), uid()]])

    def text(self, s, x, y, size=1.27, bold=False):
        self.items.append([S("text"), s, [S("exclude_from_sim"), S("no")], [S("at"), x, y, 0],
                           [S("effects"), _font(size, bold), [S("justify"), S("left"), S("top")]],
                           [S("uuid"), uid()]])

    def box(self, x1, y1, x2, y2, title):
        self.items.append([S("rectangle"), [S("start"), x1, y1], [S("end"), x2, y2],
                           [S("stroke"), [S("width"), 0], [S("type"), S("dash")]],
                           [S("fill"), [S("type"), S("none")]], [S("uuid"), uid()]])
        self.text(title, x1 + 1.27, y1 + 1.27, 2.0, True)

    # ---------------------------------------------------------------- placed parts (explicit wiring)
    def place(self, ref, lib_id, value, x, y, rot=0, footprint=None, props=None, dnp=False, in_bom=True,
              hide_ref=False, hide_val=False, fields=None):
        """Place a symbol without any wiring; returns a Part giving absolute pin positions."""
        assert ref not in self.refs, ref
        self.refs.add(ref)
        x, y = snap(x), snap(y)
        sym = self._instance(lib_id, ref, value, x, y, rot, footprint, props, in_bom=in_bom, dnp=dnp,
                             hide_ref=hide_ref, hide_val=hide_val, fields=fields)
        return Part(self, ref, sym, x, y, rot)

    def part(self, ref, lib_id, value, x, y, conns, footprint=None, props=None, dnp=False,
             stub=STUB, stubs=None, in_bom=True):
        """Place a part and connect every pin. conns: {pin_number: net | None (no-connect)}."""
        assert ref not in self.refs, ref
        self.refs.add(ref)
        x, y = snap(x), snap(y)
        sym = self._instance(lib_id, ref, value, x, y, 0, footprint, props, in_bom=in_bom, dnp=dnp)
        done = set()
        for p in pins(sym):
            num = p["number"]
            if num not in conns:
                raise KeyError("%s pin %s (%s) not assigned" % (ref, num, p["name"]))
            px, py = snap(x + p["x"]), snap(y - p["y"])
            key = (px, py)
            net = conns[num]
            self.net_pins.setdefault(net, []).append("%s.%s" % (ref, num))
            if key in done:          # stacked pins (e.g. module GND) share one stub
                continue
            done.add(key)
            if net is None:
                self.no_connect(px, py)
                continue
            d = {0: "left", 180: "right", 90: "down", 270: "up"}[int(p["angle"]) % 360]
            L = (stubs or {}).get(num, stub)
            dx, dy = {"left": (-L, 0), "right": (L, 0), "up": (0, -L), "down": (0, L)}[d]
            ex, ey = snap(px + dx), snap(py + dy)
            self.wire(px, py, ex, ey)
            if net in POWER_NETS:
                self.power(net, ex, ey, d)
            else:
                self.label(net, ex, ey, d)
        extra = set(conns) - {p["number"] for p in pins(sym)}
        if extra:
            raise KeyError("%s: unknown pins %s" % (ref, extra))

    # ---------------------------------------------------------------- output
    def save(self, path, paper="A3"):
        tb = [S("title_block"), [S("title"), self.title], [S("rev"), self.rev]]
        for i, c in enumerate(self.comments, 1):
            tb.append([S("comment"), i, c])
        doc = [S("kicad_sch"), [S("version"), 20260101], [S("generator"), "eeschema"],
               [S("generator_version"), "10.0"], [S("uuid"), self.root], [S("paper"), paper], tb,
               [S("lib_symbols")] + list(self.libs.values())]
        doc += self.items
        doc.append([S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]])
        doc.append([S("embedded_fonts"), S("no")])
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dump(doc) + "\n")
