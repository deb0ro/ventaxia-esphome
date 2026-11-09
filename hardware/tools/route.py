"""Autoroute the board with Freerouting, then clean up, pour GND and add stitching vias.
Run with KiCad's Python after build_pcb.py:  python route.py
Each stage runs in its own process (pcbnew's SWIG wrappers degrade after many removals)."""
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = os.environ.get("VENTAXIA_PRJ", "ventaxia_esp32")       # project folder = file name
PRJ = os.path.normpath(os.path.join(HERE, "..", NAME))
PCB = os.path.join(PRJ, NAME + ".kicad_pcb")
DSN = os.path.join(PRJ, NAME + ".dsn")
SES = os.path.join(PRJ, NAME + ".ses")
JAVA = os.path.join(HERE, "ext", "jdk-25.0.4.1+1-jre", "bin", "java.exe")
FR = os.path.join(HERE, "ext", "freerouting", "freerouting-2.5.0.jar")


def stage_route():
    board = pcbnew.LoadBoard(PCB)
    for t in list(board.GetTracks()):
        if not t.IsLocked():          # locked = hand-placed backbone (kept, exported as protected)
            board.Remove(t)
    # route GND as an ordinary net (pours alone end up fragmented); pours are re-created later
    for z in [z for z in board.Zones() if not z.GetIsRuleArea()]:
        board.Remove(z)
    if not pcbnew.ExportSpecctraDSN(board, DSN):
        raise SystemExit("DSN export failed")
    subprocess.run([JAVA, "-jar", FR, "--gui.enabled=false", "-de", DSN, "-do", SES,
                    "--router.autorouter.max_passes=" + os.environ.get("VENTAXIA_FR_PASSES", "30")], check=True, cwd=PRJ)
    if not pcbnew.ImportSpecctraSES(board, SES):
        raise SystemExit("SES import failed")
    pcbnew.SaveBoard(PCB, board)
    print("routed and saved")


def cleanup_dangling(board):
    """Remove (unlocked) vias connected on one layer only and track stubs ending in nothing.
    GND vias are kept - they connect to the pours. Works on plain integer coordinates."""
    TOL = pcbnew.FromMM(0.05)
    removed = 0
    for _ in range(1):              # single pass per process (SWIG breaks after removals)
        items = list(board.GetTracks())
        segs = []          # (item, net, layer, x1, y1, x2, y2, half_width, locked)
        vias = []          # (item, net, x, y, r, locked)
        for t in items:
            if t.GetClass() == "PCB_VIA":
                p = t.GetPosition()
                vias.append((t, t.GetNetname(), int(p.x), int(p.y), int(t.GetWidth(pcbnew.F_Cu)) // 2, t.IsLocked()))
            elif t.GetClass() == "PCB_TRACK":
                s_, e_ = t.GetStart(), t.GetEnd()
                segs.append((t, t.GetNetname(), t.GetLayer(), int(s_.x), int(s_.y), int(e_.x), int(e_.y),
                             int(t.GetWidth()) // 2, t.IsLocked()))
        pads = []
        for fp in board.GetFootprints():
            for p in fp.Pads():
                pads.append((p, p.GetNetname()))

        def on_seg(x, y, sg):
            _, _, _, x1, y1, x2, y2, hw, _ = sg
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            u = 0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
            px, py = x1 + u * dx, y1 + u * dy
            return (px - x) ** 2 + (py - y) ** 2 <= (hw + TOL) ** 2

        def touches(x, y, layer, net, skip):
            for sg in segs:
                if sg[0] is not skip and sg[1] == net and sg[2] == layer and on_seg(x, y, sg):
                    return True
            for v in vias:
                if v[0] is not skip and v[1] == net and (v[2] - x) ** 2 + (v[3] - y) ** 2 <= (v[4] + TOL) ** 2:
                    return True
            pt = pcbnew.VECTOR2I(x, y)
            for p, n in pads:
                if n == net and p.IsOnLayer(layer) and p.HitTest(pt, TOL):
                    return True
            return False

        dead = []
        for v in vias:
            if v[5] or v[1] == "GND":
                continue
            if not (touches(v[2], v[3], pcbnew.F_Cu, v[1], v[0]) and touches(v[2], v[3], pcbnew.B_Cu, v[1], v[0])):
                dead.append(v[0])
        for sg in segs:
            if sg[8] or sg[1] == "GND":
                continue
            if not touches(sg[3], sg[4], sg[2], sg[1], sg[0]) or not touches(sg[5], sg[6], sg[2], sg[1], sg[0]):
                dead.append(sg[0])
        if not dead:
            break
        for d in dead:
            board.Remove(d)
        removed += len(dead)
    return removed


def stage_cleanup():
    board = pcbnew.LoadBoard(PCB)
    print("removed dangling items:", cleanup_dangling(board))
    pcbnew.SaveBoard(PCB, board)


def stage_unpour():
    board = pcbnew.LoadBoard(PCB)
    for z in [z for z in board.Zones() if not z.GetIsRuleArea()]:
        board.Remove(z)
    pcbnew.SaveBoard(PCB, board)


def stage_pours():
    sys.path.insert(0, HERE)
    import importlib
    build_pcb = importlib.import_module(os.environ.get("VENTAXIA_BUILD", "build_pcb"))
    board = pcbnew.LoadBoard(PCB)
    build_pcb.add_gnd_pours(board, board.FindNet("GND"))
    zones = [z for z in board.Zones() if not z.GetIsRuleArea()]
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # GND stitching vias: grid points where both GND pours have solid copper around the via
    VIA_D, VIA_DRILL, PITCH = getattr(build_pcb, "STITCH_VIA", (0.6, 0.3, 3.0))
    gnd = board.FindNet("GND")
    fills = [z.GetFilledPolysList(z.GetLayer()) for z in zones]
    bb = board.GetBoardEdgesBoundingBox()
    r = pcbnew.FromMM(VIA_D / 2 + 0.35)
    offs = [(0, 0)] + [(int(r * c), int(r * s)) for c, s in
                       ((1, 0), (-1, 0), (0, 1), (0, -1), (0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707))]
    existing = [(t.GetPosition().x, t.GetPosition().y) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    min_d2 = pcbnew.FromMM(1.0) ** 2
    pad_boxes = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pb = pad.GetBoundingBox()
            pb.Inflate(pcbnew.FromMM(VIA_D / 2 + 0.5))
            pad_boxes.append(pb)
    # rule areas that forbid vias (board keep-outs, footprint keep-outs such as under a DC/DC module)
    rule_zones = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    for fp in board.GetFootprints():
        rule_zones += [z for z in fp.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    for z in rule_zones:
        zb = z.GetBoundingBox()
        if zb.GetWidth() > bb.GetWidth() * 0.9 or zb.GetHeight() > bb.GetHeight() * 0.9:
            continue                     # the thin edge keep-out strips: handled by the 1.5 mm grid margin
        zb.Inflate(pcbnew.FromMM(VIA_D / 2 + 0.2))
        pad_boxes.append(zb)
    n_vias = 0
    y = bb.GetY() + pcbnew.FromMM(1.5)
    while y < bb.GetBottom() - pcbnew.FromMM(1.5):
        x = bb.GetX() + pcbnew.FromMM(1.5)
        while x < bb.GetRight() - pcbnew.FromMM(1.5):
            near_pad = any(bb_.Contains(pcbnew.VECTOR2I(x, y)) for bb_ in pad_boxes) or \
                any((ex - x) ** 2 + (ey - y) ** 2 < min_d2 for ex, ey in existing)
            if not near_pad and all(f.Contains(pcbnew.VECTOR2I(x + dx, y + dy)) for f in fills for dx, dy in offs):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(x, y))
                v.SetWidth(pcbnew.FromMM(VIA_D))
                v.SetDrill(pcbnew.FromMM(VIA_DRILL))
                v.SetNet(gnd)
                board.Add(v)
                n_vias += 1
            x += pcbnew.FromMM(PITCH)
        y += pcbnew.FromMM(PITCH)
    print("GND stitching vias:", n_vias)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # second pass: join pour pieces (islands) that the grid missed - union-find over fill outlines,
    # existing GND vias / THT pads / tracks count as links, then a fine grid adds vias between
    # an F piece and a B piece that are not yet connected
    def piece(layer_idx, pt):
        f = fills2[layer_idx]
        best = None
        for i in range(f.OutlineCount()):
            ol = f.Outline(i)
            if ol.PointInside(pt):
                a = abs(ol.Area())
                if best is None or a < best[0]:
                    best = (a, i)
        return None if best is None else (layer_idx, best[1])

    zl = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"]
    layers = [z.GetLayer() for z in zl]
    fills2 = [z.GetFilledPolysList(z.GetLayer()) for z in zl]
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        if a is not None and b is not None:
            parent[find(a)] = find(b)

    def link_all(pt):
        ps = [piece(k, pt) for k in range(len(zl))]
        ps = [p for p in ps if p is not None]
        for p in ps[1:]:
            union(ps[0], p)

    for t in board.GetTracks():
        if t.GetNetname() != "GND":
            continue
        if t.GetClass() == "PCB_VIA":
            link_all(t.GetPosition())
        elif t.GetLayer() in layers:
            k = layers.index(t.GetLayer())
            union(piece(k, t.GetStart()), piece(k, t.GetEnd()))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == "GND" and pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                link_all(pad.GetPosition())
    for k in range(len(zl)):
        for i in range(fills2[k].OutlineCount()):
            find((k, i))
    existing = [(t.GetPosition().x, t.GetPosition().y) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    n2 = 0
    step = pcbnew.FromMM(0.5)
    y = bb.GetY() + pcbnew.FromMM(1.0)
    while y < bb.GetBottom() - pcbnew.FromMM(1.0):
        x = bb.GetX() + pcbnew.FromMM(1.0)
        while x < bb.GetRight() - pcbnew.FromMM(1.0):
            pt = pcbnew.VECTOR2I(x, y)
            if all(f.Contains(pcbnew.VECTOR2I(x + dx, y + dy)) for f in fills2 for dx, dy in offs) and \
                    not any(bb_.Contains(pt) for bb_ in pad_boxes) and \
                    not any((ex - x) ** 2 + (ey - y) ** 2 < min_d2 for ex, ey in existing):
                ps = [piece(k, pt) for k in range(len(zl))]
                if None not in ps and len({find(p) for p in ps}) > 1:
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pt)
                    v.SetWidth(pcbnew.FromMM(VIA_D))
                    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
                    v.SetNet(gnd)
                    board.Add(v)
                    existing.append((x, y))
                    for p in ps[1:]:
                        union(ps[0], p)
                    n2 += 1
            x += step
        y += step
    roots = {find(p) for p in list(parent)}
    print("GND island vias:", n2, "remaining pour groups:", len(roots))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)

    pcbnew.SaveBoard(PCB, board)


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage == "all":
        for st in ("route", "cleanup", "cleanup", "cleanup", "unpour", "pours"):
            subprocess.run([sys.executable, os.path.abspath(__file__), st], check=True)
        for f in (DSN, SES):
            if os.path.exists(f):
                os.remove(f)
    else:
        {"route": stage_route, "cleanup": stage_cleanup, "unpour": stage_unpour, "pours": stage_pours}[stage]()
