"""Footprint for TRACO TSR 1WI (e.g. TSR 1-4850WI), STRAIGHT pin version, after the TRACO drawing rev. 2 July 2026,
page 4 (review E-01): pins 1/2/3 at 2.54 mm pitch (0.50 x 0.25 mm), case pins 4/5 3.21 mm outside pins 1/3
(11.50 mm apart), body 12.1 x 8.6 x 17.5 mm, pin row 3.2 mm from one long side.
Case pins 4/5 are TABS 0.6 x 2.0 mm (detail A) on the body centre line, i.e. 1.1 mm (= 8.6/2 - 3.2) off the
pin row (review preorder P1). Plated slots 1.3 x 5.0 mm cover the tab +-1.1 mm on both sides plus tolerance.
Case pins 4/5 are mechanical only: TRACO gives no electrical function, so their pads have NO net.
The drawing does not tell clearly which long side is 3.2 mm from the pins, so the courtyard and the
"no tracks under the converter" keep-out cover 5.4 mm on BOTH sides of the pin row (conservative)."""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mvhr_ctrl", "mvhr_ctrl.pretty",
                   "TRACO_TSR-1WI_SIP3_CasePins.kicad_mod")
X_C = 2.54                      # body centre (pin 2)
W, D_NEAR, D_FAR = 12.1, 3.2, 5.4
HALF_D = D_FAR                  # conservative: 5.4 mm both sides
CY = 0.25                       # courtyard margin


def line(x1, y1, x2, y2, layer, w):
    return ('\t(fp_line (start %.3f %.3f) (end %.3f %.3f) (stroke (width %.2f) (type solid)) (layer "%s"))\n'
            % (x1, y1, x2, y2, w, layer))


def rect(x1, y1, x2, y2, layer, w):
    return ''.join(line(*a, layer, w) for a in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)))


def pad(num, x, shape, size, drill):
    n = '"%s"' % num
    return ('\t(pad %s thru_hole %s (at %.3f 0) (size %.2f %.2f) (drill %.2f) (layers "*.Cu" "*.Mask"))\n'
            % (n, shape, x, size, size, drill))


SLOT_W, SLOT_L, SLOT_RING = 1.3, 5.0, 0.4    # tab 0.6 x 2.0 at y = +-1.1 -> needs |y| <= 2.1 (+0.4 tolerance)


def slot(x):
    return ('\t(pad "" thru_hole oval (at %.3f 0) (size %.2f %.2f) (drill oval %.2f %.2f) (layers "*.Cu" "*.Mask"))\n'
            % (x, SLOT_W + 2 * SLOT_RING, SLOT_L + 2 * SLOT_RING, SLOT_W, SLOT_L))


xl, xr = X_C - W / 2, X_C + W / 2
s = '(footprint "TRACO_TSR-1WI_SIP3_CasePins"\n\t(version 20240108)\n\t(generator "mvhr_ctrl")\n\t(layer "F.Cu")\n'
s += ('\t(descr "TRACO TSR 1WI straight pins, SIP-3 2.54 mm + 2 case pins (4/5, no net), body 12.1x8.6x17.5 mm, '
      'TRACO drawing rev. 2026-07-02 p.4; avoid tracks under the converter")\n')
s += '\t(tags "dc-dc traco tsr1wi sip-3 case pins")\n\t(attr through_hole)\n'
s += ('\t(property "Reference" "REF**" (at %.2f %.2f 0) (layer "F.SilkS") '
      '(effects (font (size 1.2 1.2) (thickness 0.15))))\n' % (X_C, -HALF_D - 1.4))
s += ('\t(property "Value" "TRACO_TSR-1WI" (at %.2f %.2f 0) (layer "F.Fab") '
      '(effects (font (size 1.0 1.0) (thickness 0.15))))\n' % (X_C, HALF_D + 1.4))
s += rect(xl, -HALF_D, xr, HALF_D, "F.Fab", 0.10)
s += line(xl + 0.6, -0.9, xl + 0.6, 0.9, "F.Fab", 0.10)
s += rect(xl - CY, -HALF_D - CY, xr + CY, HALF_D + CY, "F.CrtYd", 0.05)
# silkscreen: body ends (12.1 mm) and a pin-1 mark; the long sides are left open (orientation of the 3.2 mm side)
s += line(xl - 0.12, -HALF_D, xl - 0.12, HALF_D, "F.SilkS", 0.15)
s += line(xr + 0.12, -HALF_D, xr + 0.12, HALF_D, "F.SilkS", 0.15)
s += line(-0.9, 1.3, 0.9, 1.3, "F.SilkS", 0.15)
s += pad("1", 0.0, "rect", 1.5, 0.8)
s += pad("2", 2.54, "circle", 1.5, 0.8)
s += pad("3", 5.08, "circle", 1.5, 0.8)
s += slot(-3.21)          # case tab 4
s += slot(5.08 + 3.21)    # case tab 5
# keep-out under the body: no tracks / vias, GND pour allowed. Two 1.2 mm corridors across the body leave the
# +Vin (pin 1) and +Vout (pin 3) tracks a straight way out; pin 2 (GND) connects through the pour.
CORR = 0.6
for x1, x2 in ((xl, -CORR), (CORR, 5.08 - CORR), (5.08 + CORR, xr)):
    s += ('\t(zone (net 0) (net_name "") (hatch edge 0.5) (connect_pads (clearance 0))\n'
          '\t\t(min_thickness 0.25) (filled_areas_thickness no)\n'
          '\t\t(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour allowed) (footprints allowed))\n'
          '\t\t(placement (enabled no) (sheetname ""))\n'
          '\t\t(fill (thermal_gap 0.5) (thermal_bridge_width 0.5))\n'
          '\t\t(layers "F.Cu" "B.Cu")\n'
          '\t\t(polygon (pts (xy %.3f %.3f) (xy %.3f %.3f) (xy %.3f %.3f) (xy %.3f %.3f))))\n'
          % (x1, -HALF_D, x2, -HALF_D, x2, HALF_D, x1, HALF_D))
s += ')\n'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8', newline='\n').write(s)
print("written", OUT)
