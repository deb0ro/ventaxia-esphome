"""Top view of J1 (34-pin box header, rev E) as placed on the board: hw/mvhr_ctrl/J1_pinout_top.svg.
Pin positions follow the PCB (pin 1 left, odd row towards the board interior, key notch on the odd side).
With the argument "en" the texts are English: J1_pinout_top_en.svg."""
import os
import sys

EN = sys.argv[1:] == ["en"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mvhr_ctrl",
                   "J1_pinout_top_en.svg" if EN else "J1_pinout_top.svg")
NC = "n.c." if EN else "nezapojeno"
TXT = {  # (Czech, English)
    "title": ("J1 - 34pin box header 2x17 (rev E), POHLED SHORA na desku",
              "J1 - 34-pin box header 2x17 (rev E), TOP VIEW of the board"),
    "sub": ("stejné číslování jako J10 na výkonové desce 439155, plochý kabel 1:1 (pin 1 na pin 1)",
            "same numbering as J10 on the power board 439155, ribbon cable 1:1 (pin 1 to pin 1)"),
    "edge": ("horní hrana desky (F1/D1 vpravo vedle J1)", "top edge of the board (F1/D1 to the right of J1)"),
    "odd": ("lichá řada", "odd row"), "even": ("sudá řada", "even row"),
    "key": ("bílý výřez = klíč boxu, míří DOVNITŘ desky (k paticím DevKitu); pin 1 = čtvercová ploška vlevo dole, △ na potisku",
            "white cut-out = key of the box, points INTO the board (towards the DevKit sockets); pin 1 = square pad bottom left, △ on the silkscreen"),
    "notes": (["24V: piny 1/2 (29 V naprázdno) -> F1 -> D1 -> TSR. GND: 5-8, 12, 20, 28, 32 "
               "(12/20 = zem motorů, na 439155 oddělené, na desce E spojené s GND).",
               "FAN1 = ODTAH (10 tacho, 14 PWM, 16 +10 V), FAN2 = PŘÍVOD (18 tacho, 22 PWM, 24 +10 V). "
               "PWM vstup motoru: 0 V = stop, +10 V = 100 %.",
               "13 LS (vypínač světla, ISP814 na 439155), 26 bypass (báze BC337 relé), "
               "30 NTC1 TEMP1 odtah (28 GND), 34 NTC2 TEMP2 venku (32 GND).",
               "Šedě = nepoužito: 3/4 +5 V z 439155, 15/17/19/21 původní čidlo SHT1x, ostatní lichá 9-33 nezapojena."],
              ["24V: pins 1/2 (29 V no load) -> F1 -> D1 -> TSR. GND: 5-8, 12, 20, 28, 32 "
               "(12/20 = motor ground, separate on 439155, joined to GND on board E).",
               "FAN1 = EXTRACT (10 tacho, 14 PWM, 16 +10 V), FAN2 = SUPPLY (18 tacho, 22 PWM, 24 +10 V). "
               "Motor PWM input: 0 V = stop, +10 V = 100 %.",
               "13 LS (light switch, ISP814 on 439155), 26 bypass (base of the relay BC337), "
               "30 NTC1 TEMP1 extract (28 GND), 34 NTC2 TEMP2 outdoor (32 GND).",
               "Grey = unused: 3/4 +5 V from 439155, 15/17/19/21 original SHT1x sensor, other odd 9-33 not connected."])}


def txt(key):
    return TXT[key][1 if EN else 0]
nets = {1: "24V", 2: "24V", 3: "(+5V)", 4: "(+5V)", 5: "GND", 6: "GND", 7: "GND", 8: "GND", 10: "FAN1 TACH",
        12: "GND", 13: "LS", 14: "FAN1 PWM", 16: "FAN1 +10V", 18: "FAN2 TACH", 20: "GND", 22: "FAN2 PWM",
        24: "FAN2 +10V", 26: "BYPASS", 28: "GND", 30: "NTC1", 32: "GND", 34: "NTC2",
        15: "(SHT1x)", 17: "(SHT1x)", 19: "(SHT1x)", 21: "(SHT1x)"}
col = {"24V": "#d62728", "GND": "#222222", "FAN1 TACH": "#1f77b4", "FAN1 PWM": "#1f77b4", "FAN1 +10V": "#1f77b4",
       "FAN2 TACH": "#2ca02c", "FAN2 PWM": "#2ca02c", "FAN2 +10V": "#2ca02c", "LS": "#9467bd", "BYPASS": "#ff7f0e",
       "NTC1": "#8c564b", "NTC2": "#8c564b"}
GREY = "#a0a0a0"
P, X0, YE, YO, H = 46, 150, 250, 315, 640
W = X0 * 2 + 16 * P
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
     f'font-family="Segoe UI,Arial,sans-serif">',
     f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
     f'<text x="{W / 2}" y="34" font-size="22" text-anchor="middle" font-weight="bold">'
     f'{txt("title")}</text>',
     f'<text x="{W / 2}" y="60" font-size="15" text-anchor="middle" fill="#555">{txt("sub")}</text>',
     f'<line x1="20" y1="110" x2="{W - 20}" y2="110" stroke="#888" stroke-dasharray="6 4"/>',
     f'<text x="{W / 2}" y="102" font-size="14" text-anchor="middle" fill="#888">{txt("edge")}</text>']
x1, x2 = X0 - 32, X0 + 16 * P + 32
s.append(f'<rect x="{x1}" y="{YE - 38}" width="{x2 - x1}" height="{YO - YE + 76}" rx="6" fill="#2b2b2b"/>')
s.append(f'<rect x="{x1 + 10}" y="{YE - 28}" width="{x2 - x1 - 20}" height="{YO - YE + 56}" fill="#4a4a4a"/>')
kx = X0 + 8 * P
s.append(f'<rect x="{kx - 45}" y="{YO + 28}" width="90" height="10" fill="#ffffff"/>')
for n in range(1, 35):
    c = (n - 1) // 2
    x = X0 + c * P
    y = YO if n % 2 else YE
    nm = nets.get(n, NC)
    cl = col.get(nm, GREY)
    if n == 1:
        s.append(f'<rect x="{x - 10}" y="{y - 10}" width="20" height="20" fill="#e8c86a" stroke="#000"/>')
    else:
        s.append(f'<circle cx="{x}" cy="{y}" r="10" fill="#e8c86a" stroke="#000"/>')
    s.append(f'<text x="{x}" y="{y + 4}" font-size="10" text-anchor="middle" font-weight="bold">{n}</text>')
    wt = "normal" if cl == GREY else "bold"
    if n % 2 == 0:
        ty = YE - 48
        s.append(f'<text x="{x}" y="{ty}" font-size="13" fill="{cl}" font-weight="{wt}" text-anchor="start" '
                 f'transform="rotate(-55 {x} {ty})">{nm}</text>')
    else:
        ty = YO + 52
        s.append(f'<text x="{x}" y="{ty}" font-size="13" fill="{cl}" font-weight="{wt}" text-anchor="end" '
                 f'transform="rotate(-55 {x} {ty})">{nm}</text>')
s.append(f'<text x="{X0 - 45}" y="{YO + 5}" font-size="13" text-anchor="end">{txt("odd")}</text>')
s.append(f'<text x="{X0 - 45}" y="{YE + 5}" font-size="13" text-anchor="end">{txt("even")}</text>')
s.append(f'<text x="{kx}" y="{YO + 145}" font-size="14" text-anchor="middle">{txt("key")}</text>')
notes = txt("notes")
for i, t in enumerate(notes):
    s.append(f'<text x="30" y="{H - 95 + i * 22}" font-size="14">{t}</text>')
s.append('</svg>')
open(OUT, 'w', encoding='utf-8').write('\n'.join(s))
print("written", OUT)
