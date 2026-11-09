"""Hand-assembly map of rev E (top view, every part with reference + value + polarity notes):
hw/mvhr_ctrl/osazovaci_mapa_revE.svg (Czech), with the argument "en" assembly_map_revE_en.svg. Run with KiCad's Python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" make_assembly_map.py [en]"""
import csv
import math
import os
import sys
import pcbnew

EN = sys.argv[1:] == ["en"]
PRJ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mvhr_ctrl"))
PCB = os.path.join(PRJ, "mvhr_ctrl.kicad_pcb")
OUT = os.path.join(PRJ, "assembly_map_revE_en.svg" if EN else "osazovaci_mapa_revE.svg")
S = 12.0                                   # px per mm
M = 40                                     # margin px
LEG_W = 760                                # legend column

CLS = {  # prefix: (body fill, label colour)
    "R": ("#f3dfb5", "#6b4a12"), "C": ("#cfe3f7", "#0d4a87"), "D": ("#dddddd", "#222222"),
    "Q": ("#e3d4f2", "#5a2a8a"), "J": ("#d3efd6", "#1d6a2c"), "U": ("#ffd8b0", "#9a4a00"),
    "F": ("#fff2a8", "#7a6500")}
NOTES = {  # polarity / orientation hints shown in the legend (checked against the pad 1 positions)
    "C1": "elektrolyt: + (delší nožička) VLEVO do čtverce, proužek − vpravo",
    "C2": "elektrolyt: + VLEVO do čtverce, proužek − vpravo",
    "C5": "elektrolyt: + VLEVO do čtverce, proužek − vpravo",
    "D1": "obousměrná TVS - libovolně",
    "D2": "proužek (katoda) VLEVO = čtvercová ploška",
    "D3": "LED: kratší nožička / plochá strana (katoda) VLEVO do čtverce",
    "Q1-Q4": "plochou stranou DOLŮ (k JST konektorům), E-B-C zleva doprava",
    "J1": "box header: výřez klíče DOLŮ (dovnitř desky), pin 1 = čtverec vlevo dole, △",
    "J2": "patice 1x22 - ESP anténou DOPRAVA", "J3": "patice 1x22",
    "J4": "JST: západka podle potisku (otvor ke kraji desky)",
    "U1": "TSR: pin 1 (+Vin) VLEVO = čtverec, strana s nápisem dolů (k paticím)",
    "F1": "PTC pojistka - libovolně"}
OUTSIDE = ("C1", "C2", "C5", "U1", "Q1", "Q2", "Q3", "Q4", "D3", "D2")   # label below the part: keep marks visible
ORDER = ["R", "D", "C (keramické)", "Q", "D3 LED", "J4-J9 JST", "J2/J3 patice", "C elektrolyty", "F1", "U1", "J1"]
TXT = {  # page texts: (Czech, English)
    "title": ("Rev E - osazovací mapa (pohled shora, strana s potiskem)",
              "Rev E - assembly map (top view, silkscreen side)"),
    "sub": ("95 × 95 mm, vše THT, pájí se zespodu. Barva = typ součástky, štítek = reference + hodnota.",
            "95 × 95 mm, all through-hole, soldered from the bottom. Colour = part type, label = reference + value."),
    "bom": ("Seznam (podle hodnoty)", "Parts (by value)"),
    "order": ("Doporučené pořadí pájení (od nejnižších)", "Recommended soldering order (lowest parts first)"),
    "tips": (["Čtvercová ploška: elektrolyt = +, dioda a LED = katoda, ostatní = pin 1.",
              "Pozice VLEVO / DOLŮ platí pro desku natočenou jako na obrázku (J1 nahoře).",
              "Patice J2/J3 pájej s nasazeným ESP (srovná je), pak ESP vyndej.",
              "Před vložením ESP: změř 24 V vstup -> 5V pin patice (4,6-4,8 V) a 3V3."],
             ["Square pad: electrolytic = +, diode and LED = cathode, others = pin 1.",
              "LEFT / DOWN refer to the board as shown (J1 at the top).",
              "Solder the J2/J3 sockets with the ESP plugged in (it aligns them), then remove the ESP.",
              "Before inserting the ESP: feed 24 V, measure the socket 5V pin (4.6-4.8 V) and 3V3."])}
if EN:
    NOTES = {
        "C1": "electrolytic: + (longer lead) LEFT into the square pad, - stripe right",
        "C2": "electrolytic: + LEFT into the square pad, - stripe right",
        "C5": "electrolytic: + LEFT into the square pad, - stripe right",
        "D1": "bidirectional TVS - either way",
        "D2": "band (cathode) LEFT = square pad",
        "D3": "LED: shorter lead / flat side (cathode) LEFT into the square pad",
        "Q1-Q4": "flat side DOWN (towards the JST connectors), E-B-C from left to right",
        "J1": "box header: key notch DOWN (into the board), pin 1 = square pad bottom left, △",
        "J2": "1x22 socket - ESP with the antenna to the RIGHT", "J3": "1x22 socket",
        "J4": "JST: latch as on the silkscreen (opening towards the board edge)",
        "U1": "TSR: pin 1 (+Vin) LEFT = square pad, printed side down (towards the sockets)",
        "F1": "PTC fuse - either way"}
    ORDER = ["R", "D", "C (ceramic)", "Q", "D3 LED", "J4-J9 JST", "J2/J3 sockets", "C electrolytic", "F1", "U1", "J1"]


def txt(key):
    return TXT[key][1 if EN else 0]


def mm(v):
    return pcbnew.ToMM(v)


board = pcbnew.LoadBoard(PCB)
bb = board.GetBoardEdgesBoundingBox()
BX, BY, BW, BH = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetWidth()), mm(bb.GetHeight())


def X(x):
    return M + (x - BX) * S


def Y(y):
    return M + 60 + (y - BY) * S


W = int(M * 2 + BW * S + LEG_W)
H = int(max(M * 2 + 60 + BH * S + 40, 1400))
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="Segoe UI,Arial,sans-serif">', f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
     f'<text x="{M}" y="{M + 10}" font-size="24" font-weight="bold">{txt("title")}</text>',
     f'<text x="{M}" y="{M + 38}" font-size="15" fill="#555">{txt("sub")}</text>']
o.append(f'<rect x="{X(BX)}" y="{Y(BY)}" width="{BW * S}" height="{BH * S}" rx="6" fill="#2f6b3a" '
         f'stroke="#000" stroke-width="2"/>')


def shape_svg(sh, col, w):
    t = sh.GetShape()
    if t == pcbnew.SHAPE_T_SEGMENT:
        a, b = sh.GetStart(), sh.GetEnd()
        return f'<line x1="{X(mm(a.x))}" y1="{Y(mm(a.y))}" x2="{X(mm(b.x))}" y2="{Y(mm(b.y))}" stroke="{col}" ' \
               f'stroke-width="{w}" stroke-linecap="round"/>'
    if t == pcbnew.SHAPE_T_CIRCLE:
        c = sh.GetCenter()
        fill = col if sh.IsSolidFill() else "none"
        return f'<circle cx="{X(mm(c.x))}" cy="{Y(mm(c.y))}" r="{mm(sh.GetRadius()) * S}" fill="{fill}" ' \
               f'stroke="{col}" stroke-width="{w}"/>'
    if t == pcbnew.SHAPE_T_ARC:
        c, r = sh.GetCenter(), mm(sh.GetRadius())
        a0 = math.atan2(mm(sh.GetStart().y) - mm(c.y), mm(sh.GetStart().x) - mm(c.x))
        da = math.radians(sh.GetArcAngle().AsDegrees())
        pts = [(mm(c.x) + r * math.cos(a0 + da * i / 24), mm(c.y) + r * math.sin(a0 + da * i / 24))
               for i in range(25)]
        p = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
        return f'<polyline points="{p}" fill="none" stroke="{col}" stroke-width="{w}"/>'
    if t in (pcbnew.SHAPE_T_RECT, pcbnew.SHAPE_T_POLY):
        if t == pcbnew.SHAPE_T_RECT:
            pts = [(mm(v.x), mm(v.y)) for v in sh.GetRectCorners()]
        else:
            ol = sh.GetPolyShape().Outline(0)
            pts = [(mm(ol.CPoint(i).x), mm(ol.CPoint(i).y)) for i in range(ol.PointCount())]
        fill = col if sh.IsSolidFill() else "none"
        p = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
        return f'<polygon points="{p}" fill="{fill}" stroke="{col}" stroke-width="{w}"/>'
    return ""


# board-level silkscreen (antenna keep-out text etc.)
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_SHAPE):
        o.append(shape_svg(d, "#ffffff", 1.2))
    elif d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_TEXT):
        p = d.GetTextPos()
        o.append(f'<text x="{X(mm(p.x))}" y="{Y(mm(p.y))}" font-size="11" fill="#ffffff" text-anchor="middle" '
                 f'dominant-baseline="middle" transform="rotate({-d.GetTextAngle().AsDegrees()} {X(mm(p.x))} '
                 f'{Y(mm(p.y))})">{d.GetShownText(False)}</text>')

labels = []
parts = []
for fp in board.GetFootprints():
    ref, val = fp.GetReference(), fp.GetValue()
    pre = ref.rstrip("0123456789")
    body, lc = CLS.get(pre, ("#eeeeee", "#000"))
    if ref.startswith("C") and val.startswith(("10u/", "47u", "100u")):
        body = "#a9c8ec"
    if ref == "D3":
        body, lc = "#ffc4c4", "#a00000"
    cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    x1, y1, w, h = mm(cy.GetX()), mm(cy.GetY()), mm(cy.GetWidth()), mm(cy.GetHeight())
    big = ref in ("J2", "J3")
    o.append(f'<rect x="{X(x1)}" y="{Y(y1)}" width="{w * S}" height="{h * S}" rx="3" fill="{body}" '
             f'fill-opacity="{0.55 if big else 0.95}" stroke="#000" stroke-width="0.8"/>')
    for it in fp.GraphicalItems():
        if it.GetLayer() == pcbnew.F_SilkS and isinstance(it, pcbnew.PCB_SHAPE):
            o.append(shape_svg(it, "#222222", 1.4))
    for pad in fp.Pads():
        p, sz = pad.GetPosition(), pad.GetSize(pcbnew.F_Cu)
        px, py, sx, sy = mm(p.x), mm(p.y), mm(sz.x) * S, mm(sz.y) * S
        rot = -pad.GetOrientation().AsDegrees()
        shp = pad.GetShape(pcbnew.F_Cu)
        tr = f'transform="rotate({rot} {X(px)} {Y(py)})"'
        if shp == pcbnew.PAD_SHAPE_CIRCLE:
            o.append(f'<circle cx="{X(px)}" cy="{Y(py)}" r="{sx / 2}" fill="#d9a520" stroke="#6b5000" '
                     f'stroke-width="0.6"/>')
        else:
            rx = min(sx, sy) / 2 if shp == pcbnew.PAD_SHAPE_OVAL else (0 if shp == pcbnew.PAD_SHAPE_RECT else 2)
            o.append(f'<rect x="{X(px) - sx / 2}" y="{Y(py) - sy / 2}" width="{sx}" height="{sy}" rx="{rx}" '
                     f'fill="#d9a520" stroke="#6b5000" stroke-width="0.6" {tr}/>')
        if pad.GetDrillSize().x > 0:
            dx, dy = mm(pad.GetDrillSize().x) * S, mm(pad.GetDrillSize().y) * S
            o.append(f'<rect x="{X(px) - dx / 2}" y="{Y(py) - dy / 2}" width="{dx}" height="{dy}" '
                     f'rx="{min(dx, dy) / 2}" fill="#ffffff" {tr}/>')
    vert = h > w * 1.6 and not big
    cxp, cyp = X(x1 + w / 2), Y(y1 + h / 2)
    if big:
        cyp = Y(y1 + h / 2) + (14 if ref == "J2" else -14)
    if ref in OUTSIDE:
        cyp = Y(y1 + h) + 17
    labels.append((cxp, cyp, ref, val, lc, vert))
    parts.append((ref, val))

for cx, cy, ref, val, lc, vert in labels:
    v = val if len(val) <= 14 else val[:14] + "…"
    tr = f' transform="rotate(-90 {cx} {cy})"' if vert else ""
    o.append(f'<g{tr}><rect x="{cx - 40}" y="{cy - 16}" width="80" height="31" rx="4" fill="#ffffff" '
             f'fill-opacity="0.88" stroke="{lc}" stroke-width="1"/>'
             f'<text x="{cx}" y="{cy - 2}" font-size="13" font-weight="bold" fill="{lc}" text-anchor="middle">'
             f'{ref}</text><text x="{cx}" y="{cy + 11}" font-size="11" fill="#111" text-anchor="middle">{v}</text></g>')

# legend: BOM grouped by value, with notes
lx = M * 2 + BW * S
ly = M + 70
o.append(f'<text x="{lx}" y="{ly}" font-size="18" font-weight="bold">{txt("bom")}</text>')
ly += 14
with open(os.path.join(PRJ, "mvhr_ctrl_bom.csv"), encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
for r in rows:
    ref, val, qty = r["Reference"], r["Value"], r["Qty"]
    pre = ref.split(",")[0].rstrip("0123456789-").rstrip("0123456789")
    body, lc = CLS.get(pre[:1], ("#eee", "#000"))
    ly += 24
    o.append(f'<rect x="{lx}" y="{ly - 14}" width="14" height="14" fill="{body}" stroke="#000" stroke-width="0.6"/>')
    o.append(f'<text x="{lx + 22}" y="{ly - 2}" font-size="13"><tspan font-weight="bold" fill="{lc}">{ref}</tspan>'
             f'  {qty}×  {val}</text>')
    note = NOTES.get(ref) or next((NOTES[k] for k in NOTES if k in ref.split(",")), None)
    if note:
        ly += 17
        o.append(f'<text x="{lx + 22}" y="{ly - 2}" font-size="12" fill="#b03000">↳ {note}</text>')
ly += 34
o.append(f'<text x="{lx}" y="{ly}" font-size="18" font-weight="bold">{txt("order")}</text>')
for i, t in enumerate(ORDER):
    ly += 21
    o.append(f'<text x="{lx}" y="{ly}" font-size="13">{i + 1}. {t}</text>')
ly += 34
for t in txt("tips"):
    o.append(f'<text x="{lx}" y="{ly}" font-size="13" fill="#333">• {t}</text>')
    ly += 20
o.append("</svg>")
open(OUT, "w", encoding="utf-8").write("\n".join(o))
print("written", OUT, len(parts), "parts")
