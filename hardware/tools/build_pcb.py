"""Create the PCB (placement only) from the schematic netlist.
Run with KiCad's Python:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_pcb.py

Coordinates are in mm, board origin = top-left corner, viewed from the FRONT
(display side). Front = F.Cu (display, buttons), back = B.Cu (everything else)."""
import os
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import find, find_all, parse  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, "..", "ventaxia_esp32"))
SCH = os.path.join(PRJ, "ventaxia_esp32.kicad_sch")
PCB = os.path.join(PRJ, "ventaxia_esp32.kicad_pcb")
NET = os.path.join(PRJ, "ventaxia_esp32.net")
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FP_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

# Board 100 x 100 behind the front cover; a 3D-printed frame in the cover opening (100.5 x 91.2) shows
# only the display and the buttons and holds the board (H5-H8). Placement coordinates are relative to the
# original 98 x 88 layout; the board extends 2 mm left and 12 mm up from it.
X0, Y0, X1, Y1 = -2.0, -12.0, 98.0, 88.0
W, H = X1 - X0, Y1 - Y0
WIN_W, WIN_H = 100.5, 91.2  # cover opening, centred on the board
OX, OY = 50.0, 50.0        # board origin on the page

# Display module MSP2807 (86 x 50, landscape, header on the left)
DISP_X, DISP_Y = 6.0, 4.0

# ---------------------------------------------------------------- explicit placement
# ref: (x, y, rotation_deg, side)   side: "F" or "B"
PLACE = {
    "J12": (DISP_X + 2.0, DISP_Y + 8.49, 0, "F"),        # display socket, pin1 = VCC (top)
    "H1": (DISP_X + 6.92, DISP_Y + 3.0, 0, "F"),
    "H2": (DISP_X + 6.92, DISP_Y + 47.0, 0, "F"),
    "H3": (DISP_X + 83.0, DISP_Y + 3.0, 0, "F"),
    "H4": (DISP_X + 83.0, DISP_Y + 47.0, 0, "F"),
    "H5": (2.0, -3.5, 0, "F"),                          # H5-H8: board -> 3D frame in the cover opening
    "H6": (94.0, -3.5, 0, "F"),
    "H7": (2.5, 79.0, 0, "F"),
    "H8": (95.0, 40.0, 0, "F"),
    "SW3": (28.0, 76.0, 0, "F"),
    "SW4": (42.0, 76.0, 0, "F"),
    "SW5": (56.0, 76.0, 0, "F"),
    "SW6": (70.0, 76.0, 0, "F"),
    # service buttons, LEDs and their resistors on the front, right of the user buttons
    "SW1": (79.0, 61.5, 0, "F"),                         # RESET
    "SW2": (87.0, 61.5, 0, "F"),                         # BOOT
    "D4": (79.0, 66.5, 0, "F"),
    "D5": (87.0, 66.5, 0, "F"),
    "R9": (79.0, 69.0, 0, "F"),
    "R10": (87.0, 69.0, 0, "F"),
    "R8": (86.0, 58.0, 0, "F"),
    # ESP32 decoupling + EN on the front, right opposite the module's 3V3/EN pads (bottom row)
    "C11": (89.3, 83.6, 90, "F"),
    "C10": (86.7, 83.6, 90, "F"),
    "R7": (78.9, 83.6, 90, "F"),
    "C12": (76.5, 83.6, 90, "F"),
    # buck TPS54360 (back), above the ESP. Flipped pads: left 1 BOOT(bottom) 2 VIN 3 EN 4 RT(top),
    # right 5 FB(top) 6 COMP 7 GND 8 SW(bottom)
    "U2": (77.0, 40.0, 0, "B"),
    "C3": (71.7, 40.3, 90, "B"),                         # 100 nF HF input cap at VIN
    "C1": (69.1, 40.3, 90, "B"),
    "C2": (66.5, 40.3, 90, "B"),
    "R1": (71.7, 37.0, 0, "B"),                          # RT 243k at pin 4
    "C5": (77.0, 44.0, 0, "B"),                          # BOOT - SW
    "D2": (83.0, 46.2, 0, "B"),                          # catch diode SW -> GND
    "L1": (86.2, 37.0, 90, "B"),                         # FXL1040 (10 x 11 mm): pad 2 (3V3_BUCK) top
    "C7": (82.0, 27.7, 90, "B"),                         # output caps on a locked 3V3_BUCK bus
    "C8": (84.4, 27.7, 90, "B"),
    "C15": (86.8, 27.7, 90, "B"),
    "C16": (89.2, 27.7, 90, "B"),
    # power mux TPS2116 right of the inductor: VIN1 (left column) faces L1, VOUT -> C25 -> backbone vias
    "U7": (93.6, 31.25, 0, "B"),
    "R50": (92.8, 25.6, 270, "B"),                       # PR1 divider from +24V: straddles the MODE loop like R51
    "R51": (94.5, 25.6, 90, "B"),                        # straddles the loop track: PR1 inside, GND outside
    "C26": (97.0, 31.0, 270, "B"),
    "U6": (95.0, 19.8, 0, "B"),                          # USB LDO next to the mux (3V3_USB stays short)
    "C23": (91.9, 19.8, 90, "B"),
    "C24": (95.4, 22.6, 180, "B"),
    "C25": (93.6, 34.3, 270, "B"),
    "C29": (29.8, 40.0, 90, "B"),                        # 22u at the CO2 connector J13
    "C30": (90.6, 15.0, 90, "B"),                        # 22u at the humidity connector J11
    "R3": (79.4, 34.9, 0, "B"),                          # FB divider at pin 5
    "R4": (79.4, 33.2, 0, "B"),
    "C18": (75.9, 35.0, 0, "B"),                         # compensation at pin 6 (over the package top)
    "R2": (75.9, 33.3, 0, "B"),
    "C17": (72.9, 33.3, 0, "B"),
    "D1": (66.0, 35.0, 0, "B"),                          # TVS
    "F1": (66.0, 31.8, 0, "B"),
    # USB: connector on the bottom edge next to the ESP, U3 in line, series R at the ESP pins
    "J2": (60.0, 84.4, 180, "B"),
    "U3": (68.0, 81.5, 0, "B"),
    "R30": (71.0, 84.6, 270, "B"),                       # D+ : U3.6 -> R30 -> U1.14 (B.Cu, no via)
    "R31": (71.0, 80.0, 90, "B"),                        # D- : U3.4 -> R31 -> via -> F.Cu -> via -> U1.13
    "R5": (53.0, 82.0, 90, "B"),
    "R6": (51.5, 82.0, 90, "B"),
}
# placed by the centre of their courtyard
CENTER = {
    "J1": (51.0, -5.0, 90, "B"),                         # 34-pin box header in the top strip
    "J11": (86.0, 18.6, 90, "B"),                        # SHT4x humidity probe (JST-XH 4)
    "J13": (22.0, 40.0, 0, "B"),                         # CO2 sensor SCD4x/SCD30 (JST-XH 4), same pinout
    "J3": (26.0, 61.0, 0, "B"),
    "J4": (37.0, 61.0, 0, "B"),
    "J5": (48.0, 61.0, 0, "B"),
    "J6": (59.0, 61.0, 0, "B"),
    "J9": (17.0, 79.0, 0, "B"),
}
ESP_POS = (X1 - 12.75, 78.0)
BACKBONE_X = 83.0                                        # x of the locked +3V3 track on F.Cu

# (x, y, text, side, size) - functional silkscreen labels
SILK_LABELS = [
    (26.0, 65.6, "OUTDOOR", "B", 1.0), (37.0, 65.6, "SUPPLY", "B", 1.0),
    (48.0, 65.6, "EXTRACT", "B", 1.0), (59.0, 65.6, "EXHAUST", "B", 1.0),
    (26.0, 56.8, "DS18B20: GND DATA 3V3", "B", 0.9),
    (51.0, 1.2, "J1 -> 439155 J10 (pin 1 = triangle)", "B", 1.0),
    (82.0, 18.6, "HUMIDITY SHT4x", "B", 0.9, 90), (80.6, 18.6, "SCL SDA GND 3V3", "B", 0.8, 90),
    (22.0, 35.9, "SCL SDA GND 3V3", "B", 0.9), (22.0, 44.6, "CO2 SCD4x", "B", 1.0),
    (11.4, 79.0, "UART 3V3", "B", 0.9, 90), (13.6, 79.0, "GND RX TX 5V GND 3V3", "B", 0.8, 90),
    (60.0, 75.6, "USB - programming only", "B", 0.8),
    (79.0, 58.3, "RST", "F", 1.0), (87.0, 64.7, "BOOT", "F", 1.0),
    (79.0, 71.0, "STATUS", "F", 0.9), (87.0, 71.0, "3V3", "F", 0.9),
    (40.0, 56.5, "MSP2807: bridge J1 on the module (3.3 V)", "F", 1.0),
]                              # ESP32 (25.5 long), antenna flush with right edge

# ---------------------------------------------------------------- auto-packed groups (back side)
GROUPS = [
    # (x1, y1, x2, y2, refs)
    (37, 4, 61, 53, ["Q1", "R20", "R21", "R22", "R23", "R24", "R25", "C21", "R26", "R27",
                      "Q2", "R40", "R41", "R42", "R43", "R44", "R45", "C41", "R46", "R47"]),
    (11, 12, 35, 53, ["R11", "R12", "R13", "R14", "C13", "R15", "R16", "C14", "R17", "R18", "R19", "C9"]),
    (22, 67, 46, 87, ["U8", "C28", "R53", "R54", "JP1", "U4", "R61", "R62", "R63", "R64", "R65", "R66", "R67", "R68", "J7", "J8", "U5"]),
]


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def load_netlist():
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", NET, SCH],
                   check=True, capture_output=True)
    t = parse(open(NET, encoding="utf-8").read())
    comps = {}
    for c in find_all(find(t, "components"), "comp"):
        ref = find(c, "ref")[1]
        comps[ref] = {
            "value": find(c, "value")[1],
            "footprint": find(c, "footprint")[1] if find(c, "footprint") else "",
            "uuid": find(c, "tstamps")[1],
        }
    pad_net = {}
    for n in find_all(find(t, "nets"), "net"):
        name = find(n, "name")[1]
        for node in find_all(n, "node"):
            pad_net[(find(node, "ref")[1], find(node, "pin")[1])] = name
    return comps, pad_net


def bbox_mm(fp):
    try:
        b = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd).BBox()
        if b.GetWidth() > 0:
            return b
    except Exception:
        pass
    return fp.GetBoundingBox(False)


def place(fp, x, y, rot, side):
    if side == "B" and not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    fp.SetOrientationDegrees(rot or 0)
    fp.SetPosition(vec(x, y))


def add_edge_keepout(board, w=0.3):
    """Rule areas along the board edge: no tracks/vias (Freerouting ignores the copper-to-edge rule)."""
    for x1, y1, x2, y2 in ((X0, Y0, X1, Y0 + w), (X0, Y1 - w, X1, Y1), (X0, Y0, X0 + w, Y1), (X1 - w, Y0, X1, Y1)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetDoNotAllowZoneFills(False)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            ol.Append(mm(OX + x), mm(OY + y))
        board.Add(z)


def add_gnd_pours(board, gnd):
    """GND pours on both layers: SMD pads solid, THT thermal, islands removed."""
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD solid, THT thermal
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((X0 + 0.5, Y0 + 0.5), (X1 - 0.5, Y0 + 0.5), (X1 - 0.5, Y1 - 0.5), (X0 + 0.5, Y1 - 0.5)):
            ol.Append(mm(OX + x), mm(OY + y))
        board.Add(z)


def pad_xy(fps, ref, num):
    p = [q for q in fps[ref].Pads() if q.GetNumber() == num][0]
    return (round(pcbnew.ToMM(p.GetPosition().x) - OX, 3), round(pcbnew.ToMM(p.GetPosition().y) - OY, 3))


def lock_track(board, net, pts, w, layer):
    for p1, p2 in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(vec(*p1)); t.SetEnd(vec(*p2)); t.SetWidth(mm(w))
        t.SetLayer(layer); t.SetNet(net); t.SetLocked(True)
        board.Add(t)


def lock_via(board, net, xy, d=0.8, drill=0.4):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(vec(*xy)); v.SetWidth(mm(d)); v.SetDrill(mm(drill)); v.SetNet(net)
    v.SetLocked(True)
    board.Add(v)


def add_3v3_backbone(board, fps, nets):
    """Locked power path (rev. C):
    L1 pad 2 -> 3V3_BUCK bus under the output caps and a wide track to the mux U7 VIN1;
    U7 VOUT (both pins, through the channel between the pad columns) -> C25 -> 2 vias ->
    F.Cu backbone down under the ESP module into C10 next to the module's 3V3 pin."""
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    buck, out, gnd = nets["3V3_BUCK"], nets["+3V3"], nets["GND"]
    lx, ly = pad_xy(fps, "L1", "2")                     # 3V3_BUCK pad (top)
    caps = [pad_xy(fps, c, "1") for c in ("C7", "C8", "C15", "C16")]
    by = caps[0][1]
    assert all(abs(c[1] - by) < 0.01 for c in caps) and by < ly, (caps, ly)
    lock_track(board, buck, [(caps[0][0], by), (caps[-1][0], by)], 1.2, B)   # bus through the cap pads
    lock_track(board, buck, [(lx, by), (lx, ly)], 2.0, B)                     # bus -> L1 pad
    vin1 = pad_xy(fps, "U7", "3")
    vo_l, vo_r = pad_xy(fps, "U7", "2"), pad_xy(fps, "U7", "7")
    g1 = pad_xy(fps, "U7", "1")
    assert vin1[0] < vo_r[0] and abs(vo_l[1] - vo_r[1]) < 0.01 and vo_l[0] < vo_r[0], (vin1, vo_l, vo_r)
    lock_track(board, buck, [(lx, vin1[1]), (vin1[0] - 1.05, vin1[1])], 0.8, B)  # L1 pad -> near VIN1
    lock_track(board, buck, [(vin1[0] - 1.05, vin1[1]), vin1], 0.3, B)
    cx = round((vo_l[0] + vo_r[0]) / 2, 3)                                      # channel between columns
    c25 = pad_xy(fps, "C25", "1")
    assert abs(c25[0] - cx) < 0.05 and c25[1] > g1[1], (c25, cx)
    lock_track(board, out, [vo_l, (cx, vo_l[1])], 0.25, B)
    lock_track(board, out, [vo_r, (cx, vo_r[1])], 0.25, B)
    lock_track(board, out, [(cx, vo_l[1]), (cx, c25[1])], 0.25, B)
    # MODE tied to VIN1: loop around the top of U7; PR1 inside, R50 (+24V) and R51 (GND) straddle the loop
    mode, pr1 = pad_xy(fps, "U7", "5"), pad_xy(fps, "U7", "4")
    r50t, r50b = pad_xy(fps, "R50", "1"), pad_xy(fps, "R50", "2")
    r51b, r51t = pad_xy(fps, "R51", "1"), pad_xy(fps, "R51", "2")
    assert r50t[1] < r50b[1] and r51t[1] < r51b[1], (r50t, r50b, r51t, r51b)
    ly_top, lx_l, lx_r = round((r51t[1] + r51b[1]) / 2, 3), vin1[0] - 1.26, mode[0] + 1.56
    lock_track(board, buck, [(lx_l, vin1[1]), (lx_l, ly_top), (lx_r, ly_top), (lx_r, mode[1]), mode], 0.25, B)
    prn = nets["MUX_PR1"]
    lock_track(board, prn, [pr1, (pr1[0], r50b[1] + 0.5), r50b], 0.25, B)
    lock_track(board, prn, [r51b, (r51b[0], r51b[1] + 0.6), (r50b[0] + 1.0, r50b[1]), r50b], 0.25, B)
    # VIN2 -> C26 -> via (3V3_USB continues from the LDO)
    vin2, c26 = pad_xy(fps, "U7", "6"), pad_xy(fps, "C26", "1")
    usb = nets["3V3_USB"]
    assert c26[1] < vin2[1], c26
    lock_track(board, usb, [vin2, (c26[0] - 0.8, vin2[1]), (c26[0] - 0.4, c26[1] + 0.38), c26], 0.3, B)
    u6o, c24 = pad_xy(fps, "U6", "5"), pad_xy(fps, "C24", "1")
    assert abs(c24[0] - u6o[0]) < 0.1, (c24, u6o)
    lock_track(board, usb, [u6o, c24, (c26[0], c24[1] + c26[0] - c24[0]), c26], 0.3, B)
    # U7 GND pin -> via left-below the package
    gv = (g1[0] - 1.25, g1[1] + 0.3)
    lock_track(board, gnd, [g1, (g1[0] - 0.6, g1[1]), gv], 0.3, B)
    lock_via(board, gnd, gv, 0.6, 0.3)
    # backbone start: 2 vias left of C25, F.Cu from there
    X = BACKBONE_X
    v1, v2 = (c25[0] - 1.8, c25[1]), (c25[0] - 1.8, c25[1] + 1.3)
    lock_track(board, out, [c25, v1, v2], 0.8, B)
    for v in (v1, v2):
        lock_via(board, out, v)
    c_pad = [p for p in fps["C10"].Pads() if p.GetNetname() == "+3V3"][0]
    cx10 = pcbnew.ToMM(c_pad.GetPosition().x) - OX
    cy10 = pcbnew.ToMM(c_pad.GetPosition().y) - OY
    lock_track(board, out, [v1, v2], 0.8, F)
    lock_track(board, out, [v2, (X, v2[1]), (X, 76.0)], 1.5, F)
    lock_track(board, out, [(X, 76.0), (85.2, 76.0), (85.2, cy10), (cx10, cy10)], 1.0, F)
    # C10 -> C11 -> via -> ESP 3V3 pin (pad at the board edge; the edge keepout blocks the autorouter)
    c11 = [p for p in fps["C11"].Pads() if p.GetNetname() == "+3V3"][0]
    c11 = (round(pcbnew.ToMM(c11.GetPosition().x) - OX, 3), round(pcbnew.ToMM(c11.GetPosition().y) - OY, 3))
    u1p = pad_xy(fps, "U1", "2")
    ev = (u1p[0], u1p[1] - 1.45)
    lock_track(board, out, [(cx10, cy10), (c11[0], cy10), c11], 1.0, F)
    lock_track(board, out, [c11, ev], 0.8, F)
    lock_via(board, out, ev)
    lock_track(board, out, [ev, u1p], 0.8, B)
    # front parts right of the backbone (R8, R10) are boxed in by the antenna keep-out:
    # tie their +3V3 pads straight to the backbone
    for ref in ("R8", "R10"):
        pad = [q for q in fps[ref].Pads() if q.GetNetname() == "+3V3"][0]
        px = pcbnew.ToMM(pad.GetPosition().x) - OX
        py = pcbnew.ToMM(pad.GetPosition().y) - OY
        lock_track(board, out, [(X, py), (px, py)], 0.5, F)
    print("power locks: L1.2", (lx, ly), "caps y", by, "U7 VIN1", vin1, "VOUT", vo_l, vo_r, "C25", c25)


def add_usb_pair(board, fps, nets):
    """Locked USB D+/D- (rev. C, review B-04): pair leaves the connector downwards (0.5 mm pitch),
    runs under the connector body between the shell pads to U3 (flow-through), D+ stays on B.Cu
    through R30 into U1.14, D- needs one layer change (U1.13 is only reachable from under the module)."""
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    n = {k: nets[k] for k in ("USB_DP_C", "USB_DN_C", "USB_DP_P", "USB_DN_P", "USB_DP", "USB_DN", "GND", "VBUS")}
    W = 0.25
    a6, b6, a7, b7 = (pad_xy(fps, "J2", k) for k in ("A6", "B6", "A7", "B7"))
    assert b6[0] < a7[0] < a6[0] < b7[0], (b6, a7, a6, b7)
    u1, u3, u4, u5, u6, u2 = (pad_xy(fps, "U3", k) for k in ("1", "3", "4", "5", "6", "2"))
    yp, yn = 83.4, 82.9                                  # D+ / D- run below the connector pads
    xr = u1[0] - 0.76                                    # D+ riser just left of U3 pin 1
    # D+ : B6 main, A6 joined over the top of A7
    lock_track(board, n["USB_DP_C"], [a6, (a6[0], 79.0), (b6[0], 79.0), b6], W, B)
    lock_track(board, n["USB_DP_C"], [b6, (b6[0], yp - 0.4), (b6[0] + 0.4, yp), (xr - 0.4, yp),
                                      (xr, yp - 0.4), (xr, u1[1]), u1], W, B)
    # D- : A7 main, B7 joined underneath A6
    lock_track(board, n["USB_DN_C"], [b7, (b7[0], 81.5), (a7[0], 81.5)], W, B)
    lock_track(board, n["USB_DN_C"], [a7, (a7[0], yn - 0.4), (a7[0] + 0.4, yn), (xr - 0.9, yn),
                                      (xr - 0.5, yn - 0.4), (xr - 0.5, u3[1] + 0.4), (xr - 0.1, u3[1]), u3], W, B)
    # U3 GND pin -> channel between the pad columns -> via above the package
    cx = round((u2[0] + u5[0]) / 2, 3)
    gv = (cx, u3[1] - 1.15)
    lock_track(board, n["GND"], [u2, (cx, u2[1]), gv], W, B)
    lock_via(board, n["GND"], gv, 0.6, 0.3)
    # U3 VBUS pin -> via between the D-/D+ exits
    vv = (u5[0] + 0.96, u5[1] + 0.1)
    lock_track(board, n["VBUS"], [u5, vv], 0.3, B)
    lock_via(board, n["VBUS"], vv, 0.6, 0.3)
    # D+ : U3.6 -> R30 -> U1.14 (all B.Cu)
    r30a, r30b = pad_xy(fps, "R30", "1"), pad_xy(fps, "R30", "2")
    e14 = pad_xy(fps, "U1", "14")
    assert r30a[1] < r30b[1], (r30a, r30b)
    lock_track(board, n["USB_DP_P"], [u6, (r30a[0] - 0.7, u6[1]), (r30a[0], u6[1] + 0.7), r30a], W, B)
    lock_track(board, n["USB_DP"], [r30b, (r30b[0], e14[1] - 0.55), (r30b[0] + 0.55, e14[1]), e14], W, B)
    # D- : U3.4 -> R31 -> via -> F.Cu -> via above U1.13
    r31a, r31b = pad_xy(fps, "R31", "1"), pad_xy(fps, "R31", "2")
    e13 = pad_xy(fps, "U1", "13")
    assert r31a[1] > r31b[1], (r31a, r31b)
    lock_track(board, n["USB_DN_P"], [u4, (r31a[0], u4[1])], W, B)
    va, vb = (r31b[0], r31b[1] - 1.15), (e13[0], e13[1] - 1.4)
    lock_track(board, n["USB_DN"], [r31b, va], W, B)
    lock_via(board, n["USB_DN"], va, 0.6, 0.3)
    dy = vb[1] - va[1]
    dx = vb[0] - va[0]
    lock_track(board, n["USB_DN"], [va, (vb[0], va[1] + dx), vb], W, F)
    lock_via(board, n["USB_DN"], vb, 0.6, 0.3)
    lock_track(board, n["USB_DN"], [vb, e13], W, B)
    print("usb locks: J2", b6, a7, a6, b7, "U3", u1, u3, "R30", r30a, r30b, "R31", r31a, r31b, "U1", e14, e13, dy)


KEEP_SILK_REF = {"J1", "J7", "J8", "J12", "SW3", "SW4", "SW5", "SW6"}


def add_silk(board, fps):
    """Readable silkscreen: references only on main connectors/controls (others on the fab layer),
    functional labels, and footprint silk lines removed where they hit pads or the board edge."""
    edge = board.GetBoardEdgesBoundingBox()
    edge.Inflate(-mm(0.25))
    pads = {True: [], False: []}
    for fp in fps.values():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            bb.Inflate(mm(0.0))
            if p.IsOnLayer(pcbnew.F_Cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                pads[False].append(bb)
            if p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                pads[True].append(bb)
    for ref, fp in fps.items():
        if ref not in KEEP_SILK_REF:
            fp.Reference().SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
        fp.Value().SetVisible(False)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                continue
            bb = item.GetBoundingBox()
            back = item.GetLayer() == pcbnew.B_SilkS
            if not edge.Contains(bb) or any(bb.Intersects(pb) for pb in pads[back]):
                item.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
    for lab in SILK_LABELS:
        x, y, text, side, size = lab[:5]
        t = pcbnew.PCB_TEXT(board)
        if len(lab) > 5:
            t.SetTextAngleDegrees(lab[5])
        t.SetText(text)
        t.SetPosition(vec(x, y))
        t.SetLayer(pcbnew.B_SilkS if side == "B" else pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(0.15 if size < 1.2 else 0.18))
        if side == "B":
            t.SetMirrored(True)
        board.Add(t)


def main():
    comps, pad_net = load_netlist()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_MinClearance = mm(0.2)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.2)          # ESP32 thermal vias

    nets = {}
    for name in sorted(set(pad_net.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni
    for name in list(nets):                 # local labels: also reachable without the sheet prefix
        if name.startswith("/"):
            nets.setdefault(name[1:], nets[name])

    fps = {}
    for ref, c in comps.items():
        lib, name = c["footprint"].split(":", 1)
        fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), name)
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

    # ESP32 footprint thermal vias 0.2 -> 0.3 mm drill (pad 0.6): avoids the JLCPCB small-hole surcharge
    for pad in fps["U1"].Pads():
        if pad.GetDrillSize().x == mm(0.2):
            pad.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
    ds.m_MinThroughDrill = mm(0.3)

    # explicit placements
    for ref, (x, y, rot, side) in PLACE.items():
        place(fps[ref], x, y, rot, side)
    for ref, (x, y, rot, side) in CENTER.items():
        fp = fps[ref]
        place(fp, x, y, rot, side)
        c = bbox_mm(fp).Centre()
        place(fp, x - pcbnew.ToMM(c.x) + OX + x, y - pcbnew.ToMM(c.y) + OY + y, rot, side)

    # ESP32: the pad row 15..26 is at the end opposite the antenna -> put it on the left
    fp = fps["U1"]
    for r in (0, 90, 180, 270):
        place(fp, ESP_POS[0], ESP_POS[1], r, "B")
        row = [p.GetPosition().x for p in fp.Pads() if p.GetNumber().isdigit() and 15 <= int(p.GetNumber()) <= 26]
        if pcbnew.ToMM(sum(row) / len(row)) - OX < ESP_POS[0] - 5:
            break

    # auto-pack groups (rows, left->right, top->bottom)
    gap = 0.6
    for x1, y1, x2, y2, refs in GROUPS:
        cx, cy, row_h = x1, y1, 0.0
        for ref in refs:
            fp = fps[ref]
            place(fp, 0, 0, 0, "B")
            b = bbox_mm(fp)
            w, h = pcbnew.ToMM(b.GetWidth()), pcbnew.ToMM(b.GetHeight())
            offx = pcbnew.ToMM(fp.GetPosition().x - b.GetX())
            offy = pcbnew.ToMM(fp.GetPosition().y - b.GetY())
            if cx + w > x2 and cx > x1:
                cx, cy, row_h = x1, cy + row_h + gap, 0.0
            if cy + h > y2:
                print("WARNING: group overflow at", ref)
            place(fp, cx + offx, cy + offy, 0, "B")
            cx += w + gap
            row_h = max(row_h, h)

    missing = set(fps) - set(PLACE) - set(CENTER) - {"U1"} - {r for g in GROUPS for r in g[4]}
    if missing:
        print("WARNING: unplaced", sorted(missing))

    # board outline with rounded corners
    r = 2.0
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(vec(x1, y1)); s.SetEnd(vec(x2, y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)
    def arc(cx, cy, sx, sy, ang):
        a = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        a.SetCenter(vec(cx, cy)); a.SetStart(vec(sx, sy)); a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1))
        board.Add(a)
    seg(X0 + r, Y0, X1 - r, Y0); seg(X1, Y0 + r, X1, Y1 - r); seg(X1 - r, Y1, X0 + r, Y1); seg(X0, Y1 - r, X0, Y0 + r)
    arc(X0 + r, Y0 + r, X0, Y0 + r, 90); arc(X1 - r, Y0 + r, X1 - r, Y0, 90)
    arc(X1 - r, Y1 - r, X1, Y1 - r, 90); arc(X0 + r, Y1 - r, X0 + r, Y1, 90)

    # display outline on the front silkscreen (user drawing layer)
    for (x1, y1, x2, y2) in [(DISP_X, DISP_Y, DISP_X + 86, DISP_Y + 50)]:
        rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
        rect.SetStart(vec(x1, y1)); rect.SetEnd(vec(x2, y2))
        rect.SetLayer(pcbnew.Dwgs_User); rect.SetWidth(mm(0.15))
        board.Add(rect)
    wx, wy = (X0 + X1) / 2, (Y0 + Y1) / 2
    win = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    win.SetStart(vec(wx - WIN_W / 2, wy - WIN_H / 2)); win.SetEnd(vec(wx + WIN_W / 2, wy + WIN_H / 2))
    win.SetLayer(pcbnew.Dwgs_User); win.SetWidth(mm(0.15))
    board.Add(win)
    wt = pcbnew.PCB_TEXT(board)
    wt.SetText("Cover opening 100.5 x 91.2 (3D frame)")
    wt.SetPosition(vec(wx, wy + WIN_H / 2 - 1.5)); wt.SetLayer(pcbnew.Dwgs_User)
    board.Add(wt)
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("Display MSP2807 2.8\" (86x50) - front view")
    txt.SetPosition(vec(DISP_X + 43, DISP_Y + 25)); txt.SetLayer(pcbnew.Dwgs_User)
    board.Add(txt)

    add_3v3_backbone(board, fps, nets)
    add_usb_pair(board, fps, nets)
    for ref in ("J1", "J2", "J3", "J4", "J5", "J6", "J11", "J13"):                         # GND pins solid into both pours
        fps[ref].SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    add_silk(board, fps)

    add_gnd_pours(board, nets["GND"])
    add_edge_keepout(board)

    import sync_pcb
    sync_pcb.apply(board, sync_pcb.netlist_components())   # LCSC/MPN fields

    board.SetFileName(PCB)
    pcbnew.SaveBoard(PCB, board)
    print("saved", PCB, "footprints:", len(fps))


if __name__ == "__main__":
    main()
