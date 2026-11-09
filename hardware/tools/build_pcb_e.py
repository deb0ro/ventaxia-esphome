"""Rev E: MVHR control board, through-hole only - create the PCB (placement only) from the schematic netlist.
Run with KiCad's Python:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb_e.py
then route:  VENTAXIA_PRJ=mvhr_ctrl VENTAXIA_BUILD=build_pcb_e python route.py

Coordinates in mm, origin = top-left board corner, top view. Everything is through-hole and sits on the top side.
TARGET JLCPCB (17.10.2026, capabilities page): 2 layers, 1.6 mm FR4, 1 oz, track/space >= 0.10 mm, via annular
ring >= 0.18 (0.25 recommended) -> vias 0.8/0.4 (0.2; 0.9 made the board unroutable), PTH pad-hole >= 0.25, hole-to-hole 0.45, copper to routed edge >= 0.2,
NPTH >= 0.5 mm, silkscreen >= 0.15 mm / 1.0 mm text, solder mask 1:1 (JLC CAM adds its own expansion).
The board still meets the Gatema standard class listed below (set MASK_EXPANSION = 0.05 and 1.5 mm for Gatema):
Rules follow the Gatema PCB designer handbook (2026) STANDARD class, so no surcharge: 2 layers, 1.5 mm FR4,
18/18 um Cu, clearance >= 0.20 mm, tracks 0.25 (>= 0.15 at pads; the price list charges below 0.15 mm), annular ring >= 0.15 mm counted
from the DRILL = finished hole + 0.1 mm (Gatema p. 8; TO-92 therefore with 2.54 mm pitch), vias 0.8/0.4 mm,
solder mask 0.05 mm per side, copper >= 0.5 mm from the edge, outline line 0.2 mm, silkscreen >= 0.15 mm lines, ONE silk side.
The DevKit sits in two 1x22 sockets (rows 22.86 mm apart), pin 1 = antenna end on the right; no copper under the
antenna between the rows. No manufacturer name anywhere on the board."""
import os
import subprocess
import sys

os.environ.setdefault("VENTAXIA_PRJ", "mvhr_ctrl")
import pcbnew  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pcb import CLI, FP_DIR, bbox_mm  # noqa: E402
from sexp import find, find_all, parse  # noqa: E402

NAME = "mvhr_ctrl"
PRJ = os.path.normpath(os.path.join(HERE, "..", NAME))
SCH = os.path.join(PRJ, NAME + ".kicad_sch")
PCB = os.path.join(PRJ, NAME + ".kicad_pcb")
NET = os.path.join(PRJ, NAME + ".net")

X0, Y0, X1, Y1 = 0.0, 0.0, 95.0, 95.0      # 95 x 95 since 17.10.2026 (was 66 high)
OX, OY = 50.0, 50.0                # board origin on the page
STITCH_VIA = (0.9, 0.4, 4.0)       # route.py: GND stitching vias (annular 0.25 = JLC recommendation)
BOARD_THICKNESS = 1.6              # JLC offers 0.4/0.6/0.8/1.0/1.2/1.6/2.0 (Gatema standard is 1.5)
MASK_EXPANSION = 0.0               # JLC: 1:1 (their CAM expands); Gatema wants 0.05
EDGE_CU = 0.5                      # copper to board edge (Gatema: >= 0.2 milled, 0.5 scored)

# DevKit sockets: pin 1 (antenna end) on the right, pins running to the left at 2.54 mm
PIN1_X = X1 - 3.0
ROW_J2, ROW_J3 = 30.0, 30.0 + 22.86     # J2 = DevKit J1 header (3V3 ... 5V, G) on top, J3 = DevKit J3 below
ANTENNA = (PIN1_X - 8.0, ROW_J2 + 2.0, X1, ROW_J3 - 2.0)   # copper keep-out under the module antenna

CENTER = {
    "J1": (34.5, 6.6, 90),         # 34-pin box header along the top edge (x 8.6..60.4, y 1.6..11.6)
    "J8": (14.5, 88.5, 0),         # SHT4x
    "J9": (28.5, 88.5, 0),         # SCD41
    "J4": (42.0, 88.5, 0),         # DS18B20 OUTDOOR
    "J5": (54.0, 88.5, 0),         # SUPPLY
    "J6": (66.0, 88.5, 0),         # EXTRACT
    "J7": (78.0, 88.5, 0),         # EXHAUST
    "C5": (22.0, 76.0, 0),         # SCD41 charge, near J9
    "D3": (32.0, 76.0, 0),         # status LED
    # 24 V -> PTC -> TVS -> C1 -> TSR -> Schottky -> C2 -> DevKit 5V pin; C3 at the DevKit 3V3 pins
    "F1": (67.0, 4.0, 0), "D1": (80.2, 4.0, 0),
    "C1": (66.5, 12.5, 0), "U1": (78.0, 12.5, 0), "C2": (89.5, 13.5, 0),
    "D2": (70.0, 22.5, 0), "C3": (88.0, 23.5, 0),
    # bypass + light switch input, between J1 and the top socket
    "R11": (43.5, 17.0, 0), "R12": (54.5, 17.0, 0), "R13": (43.5, 23.0, 0), "R14": (54.5, 23.0, 0),
    # fans BELOW the DevKit (no height limit any more; nothing sits under the module)
    # run switches Q3/Q4 (preorder P2) left of the bottom socket: GPIO -> R20/R40 4k7 -> Q3/Q4, R25/R45 10k
    "R20": (8.5, 57.0, 0), "Q3": (18.5, 57.0, 0), "R25": (28.0, 57.0, 0),
    "R40": (8.5, 65.0, 0), "Q4": (18.5, 65.0, 0), "R45": (28.0, 65.0, 0),
    "R22": (44.6, 61.0, 0), "R21": (66.2, 61.0, 0), "R23": (77.0, 61.0, 0),
    "R24": (87.8, 61.0, 0),
    "Q1": (44.0, 68.0, 0), "C21": (54.0, 68.0, 0), "R44": (66.2, 68.0, 0), "Q2": (77.0, 68.0, 0),
    "C41": (87.0, 68.0, 0),
    "R42": (44.6, 75.0, 0), "R41": (66.2, 75.0, 0), "R43": (77.0, 75.0, 0),
}
PLACE = {"H1": (3.5, 3.5, 0), "H2": (X1 - 3.5, 3.5, 0), "H3": (3.5, Y1 - 3.5, 0), "H4": (X1 - 3.5, Y1 - 3.5, 0)}
GROUPS = [
    # (x1, y1, x2, y2, refs) auto-packed in rows (left to right, top to bottom), rows GROUP_VGAP apart
    (2.0, 15.0, 36.5, 72.0, ["R15", "R9", "C14", "R16", "R10", "C15", "R19", "C13", "R17", "R18", "R7", "R8",
                             "R60", "R61", "R62", "R63", "R64"]),                            # NTC, LED, LS, I2C, 1-Wire
]
GROUP_VGAP = 2.6                   # room for the reference above each part (review E-09: readable after assembly)
# reference position: "above" the body by default (readable after assembly); exceptions:
REF_SIDE = {"C5": "left", "D3": "right", "U1": "inside", "F1": "centre", "D1": "centre"}
SILK = [
    # (x, y, text, size[, angle])
    (14.5, Y1 - 1.4, "SHT4x", 1.2), (28.5, Y1 - 1.4, "SCD41", 1.2),
    (42.0, Y1 - 1.4, "OUTDOOR", 1.2), (54.0, Y1 - 1.4, "SUPPLY", 1.2),
    (66.0, Y1 - 1.4, "EXTRACT", 1.2), (78.0, Y1 - 1.4, "EXHAUST", 1.2),
    (89.5, ROW_J2 + 11.43, "ESP32-S3 antenna", 1.2, 90),
    (50.0, 82.3, "VA MVHR control board rev E", 1.8),
]


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def load_netlist():
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", NET, SCH],
                   check=True, capture_output=True)
    t = parse(open(NET, encoding="utf-8").read())
    os.remove(NET)
    comps = {}
    for c in find_all(find(t, "components"), "comp"):
        comps[find(c, "ref")[1]] = {"value": find(c, "value")[1], "footprint": find(c, "footprint")[1],
                                    "uuid": find(c, "tstamps")[1]}
    pad_net = {}
    for n in find_all(find(t, "nets"), "net"):
        for node in find_all(n, "node"):
            pad_net[(find(node, "ref")[1], find(node, "pin")[1])] = find(n, "name")[1]
    return comps, pad_net


def place(fp, x, y, rot):
    fp.SetOrientationDegrees(rot or 0)
    fp.SetPosition(vec(x, y))


def pad_x(fp, num):
    return pcbnew.ToMM([p for p in fp.Pads() if p.GetNumber() == num][0].GetPosition().x) - OX


def rule_area(board, rect, tracks=True, vias=True, pour=True):
    x1, y1, x2, y2 = rect
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetDoNotAllowZoneFills(pour)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        ol.Append(mm(OX + x), mm(OY + y))
    board.Add(z)


def add_edge_keepout(board, w=EDGE_CU):
    """Rule areas along the board edge: no tracks/vias (Freerouting ignores the copper-to-edge rule)."""
    for r in ((X0, Y0, X1, Y0 + w), (X0, Y1 - w, X1, Y1), (X0, Y0, X0 + w, Y1), (X1 - w, Y0, X1, Y1)):
        rule_area(board, r, pour=False)


def add_gnd_pours(board, gnd):
    """Solid GND pours on both layers (Gatema: solid, not hatched), THT thermal reliefs, islands removed."""
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        e = EDGE_CU
        for x, y in ((X0 + e, Y0 + e), (X1 - e, Y0 + e), (X1 - e, Y1 - e), (X0 + e, Y1 - e)):
            ol.Append(mm(OX + x), mm(OY + y))
        board.Add(z)


def add_silk(board, fps):
    """References stay on the silkscreen (hand assembly), 1.2 mm / 0.15 mm (Gatema minimum 1.2 / 0.13)."""
    edge = board.GetBoardEdgesBoundingBox()
    edge.Inflate(-mm(0.25))
    pads = [p.GetBoundingBox() for fp in fps.values() for p in fp.Pads()]
    for ref, fp in fps.items():
        r = fp.Reference()
        if ref.startswith("H") or ref in ("J2", "J3"):
            r.SetVisible(False)               # sockets: the DevKit outline / title name them
        r.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
        r.SetTextThickness(mm(0.15))
        if not ref.startswith("J"):           # small parts: reference centred on the body
            cy = fp.GetCourtyard(pcbnew.F_CrtYd)
            bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
            c = bb.Centre()
            side = REF_SIDE.get(ref, "above")
            if side == "left":
                c = pcbnew.VECTOR2I(bb.GetX() - mm(1.6), c.y)
            elif side == "right":
                c = pcbnew.VECTOR2I(bb.GetRight() + mm(1.6), c.y)
            elif side == "inside":              # on the body, clear of the pin row (tall part, no neighbours)
                c = pcbnew.VECTOR2I(c.x, c.y - mm(3.2))
            elif side == "centre":
                pass
            elif side == "above":
                c = pcbnew.VECTOR2I(c.x, bb.GetY() - mm(0.7))
            r.SetPosition(c)
            r.SetTextAngleDegrees(0)
        v = fp.Value()                         # assembly drawing (F.Fab): value under the part, not on the silk
        v.SetLayer(pcbnew.F_Fab)
        v.SetVisible(not ref.startswith("H"))
        v.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        v.SetTextThickness(mm(0.12))
        cyv = fp.GetCourtyard(pcbnew.F_CrtYd)
        bbv = cyv.BBox() if cyv.OutlineCount() else fp.GetBoundingBox(False)
        v.SetPosition(pcbnew.VECTOR2I(bbv.Centre().x, bbv.Centre().y + mm(0.9)))
        v.SetTextAngleDegrees(0)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() == pcbnew.F_SilkS:
                if item.GetClass() in ("PCB_TEXT", "FP_TEXT"):
                    if item.GetTextHeight() < mm(1.2):     # e.g. the "K" mark of the diodes
                        item.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
                        item.SetTextThickness(mm(0.15))
                    continue
                if hasattr(item, "GetWidth") and item.GetWidth() < mm(0.15):
                    item.SetWidth(mm(0.15))
                bb = item.GetBoundingBox()
                if not edge.Contains(bb) or any(bb.Intersects(pb) for pb in pads):
                    item.SetLayer(pcbnew.F_Fab)
    for lab in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(lab[2])
        t.SetPosition(vec(lab[0], lab[1]))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(lab[3]), mm(lab[3])))
        t.SetTextThickness(mm(0.15 if lab[3] < 1.8 else 0.18))
        if len(lab) > 4:
            t.SetTextAngleDegrees(lab[4])
        board.Add(t)


def courtyard_overlaps(fps):
    boxes = {}
    for ref, fp in fps.items():
        b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else bbox_mm(fp)
        boxes[ref] = b
    refs = sorted(boxes)
    bad = []
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if boxes[a].Intersects(boxes[b]):
                bad.append((a, b))
    return bad


def main():
    comps, pad_net = load_netlist()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(BOARD_THICKNESS))
    ds.m_TrackMinWidth = mm(0.15)            # Gatema standard 150 um, no surcharge
    ds.m_MinClearance = mm(0.2)
    ds.m_ViasMinSize = mm(0.9)
    ds.m_MinThroughDrill = mm(0.4)
    ds.m_CopperEdgeClearance = mm(EDGE_CU)
    ds.m_SolderMaskExpansion = mm(MASK_EXPANSION)
    tb = board.GetTitleBlock()
    tb.SetTitle("VA MVHR control board")
    tb.SetRevision("E")
    tb.SetDate("2026-10-17")
    board.SetTitleBlock(tb)

    nets = {}
    for name in sorted(set(pad_net.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    fps = {}
    for ref, c in comps.items():
        lib, name = c["footprint"].split(":", 1)
        lib_dir = os.path.join(PRJ, lib + ".pretty") if lib == NAME else os.path.join(FP_DIR, lib + ".pretty")
        fp = pcbnew.FootprintLoad(lib_dir, name)
        if fp is None:
            raise RuntimeError("footprint not found: " + c["footprint"])
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        for pad in fp.Pads():
            net = pad_net.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
        board.Add(fp)
        fps[ref] = fp

    for ref, (x, y, rot) in PLACE.items():
        place(fps[ref], x, y, rot)
    for ref, (x, y, rot) in CENTER.items():
        fp = fps[ref]
        place(fp, x, y, rot)
        c = bbox_mm(fp).Centre()
        place(fp, 2 * x - pcbnew.ToMM(c.x) + OX, 2 * y - pcbnew.ToMM(c.y) + OY, rot)

    for ref, y in (("J2", ROW_J2), ("J3", ROW_J3)):
        fp = fps[ref]
        for rot in (90, 270):
            place(fp, PIN1_X, y, rot)
            if pad_x(fp, "22") < PIN1_X - 50:
                break
        else:
            raise RuntimeError("socket orientation")

    gap = 0.8
    for x1, y1, x2, y2, refs in GROUPS:
        cx, cy, row_h = x1, y1, 0.0
        for ref in refs:
            fp = fps[ref]
            place(fp, 0, 0, 0)
            b = bbox_mm(fp)
            w, h = pcbnew.ToMM(b.GetWidth()), pcbnew.ToMM(b.GetHeight())
            offx = pcbnew.ToMM(fp.GetPosition().x - b.GetX())
            offy = pcbnew.ToMM(fp.GetPosition().y - b.GetY())
            if cx + w > x2 and cx > x1:
                cx, cy, row_h = x1, cy + row_h + GROUP_VGAP, 0.0
            if cy + h > y2:
                print("WARNING: group overflow at", ref, "(%.1f > %.1f)" % (cy + h, y2))
            place(fp, cx + offx, cy + offy, 0)
            cx += w + gap
            row_h = max(row_h, h)

    missing = set(fps) - set(PLACE) - set(CENTER) - {"J2", "J3"} - {r for g in GROUPS for r in g[4]}
    if missing:
        print("WARNING: unplaced", sorted(missing))
    for a, b in courtyard_overlaps(fps):
        print("WARNING: courtyard overlap", a, b)

    r = 2.0
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(vec(x1, y1)); s.SetEnd(vec(x2, y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.2))
        board.Add(s)
    def arc(cx, cy, sx, sy, ang):
        a = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        a.SetCenter(vec(cx, cy)); a.SetStart(vec(sx, sy)); a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.2))
        board.Add(a)
    seg(X0 + r, Y0, X1 - r, Y0); seg(X1, Y0 + r, X1, Y1 - r); seg(X1 - r, Y1, X0 + r, Y1); seg(X0, Y1 - r, X0, Y0 + r)
    arc(X0 + r, Y0 + r, X0, Y0 + r, 90); arc(X1 - r, Y0 + r, X1 - r, Y0, 90)
    arc(X1 - r, Y1 - r, X1, Y1 - r, 90); arc(X0 + r, Y1 - r, X0 + r, Y1, 90)

    # DevKit outline (62.74 x 25.40, pins 1.27 mm from the long edges, pin 1 ~1.4 mm from the antenna end)
    mid = (ROW_J2 + ROW_J3) / 2
    rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    rect.SetStart(vec(PIN1_X + 1.4, mid - 12.7)); rect.SetEnd(vec(PIN1_X + 1.4 - 62.74, mid + 12.7))
    rect.SetLayer(pcbnew.Dwgs_User); rect.SetWidth(mm(0.15))
    board.Add(rect)

    # review E-09: all THT pads keep thermal reliefs (the pour default) - easier hand soldering / desoldering
    add_silk(board, fps)
    add_gnd_pours(board, nets["GND"])
    add_edge_keepout(board)
    rule_area(board, ANTENNA)                  # nothing under the ESP32-S3 module antenna

    import sync_pcb
    sync_pcb.apply(board, sync_pcb.netlist_components())

    board.SetFileName(PCB)
    pcbnew.SaveBoard(PCB, board)
    # explicit stackup with the surface finish (the Python API has no setter; review E: gbrjob said Finish None)
    t = open(PCB, encoding="utf-8").read()
    if "(stackup" not in t:
        stack = ('\t\t(stackup\n'
                 '\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))\n'
                 '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))\n'
                 '\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))\n'
                 '\t\t\t(layer "dielectric 1" (type "core") (thickness %.2f) (material "FR4") (epsilon_r 4.5) '
                 '(loss_tangent 0.02))\n'
                 '\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))\n'
                 '\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))\n'
                 '\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))\n'
                 '\t\t\t(copper_finish "HAL lead-free")\n'
                 '\t\t\t(dielectric_constraints no)\n'
                 '\t\t)\n') % (BOARD_THICKNESS - 0.09)
        i = t.index("(setup") + len("(setup")
        t = t[:i] + "\n" + stack + t[i:].lstrip("\n")
        open(PCB, "w", encoding="utf-8", newline="\n").write(t)
    print("saved", PCB, "footprints:", len(fps))


if __name__ == "__main__":
    main()
