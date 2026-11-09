"""Schematic of rev. E: MVHR control board, THROUGH-HOLE ONLY (home assembly), ESP32-S3-DevKitC-1 in sockets.
Mates with the 34-pin ribbon from power board 439155 (J10). Replaces control board 439150. No display, no buttons.

Based on the alpha prototype (PN2222A drive, tacho, bypass, NTC - proven in the unit 16.10.2026) and rev D1, with
the review fixes: fans NOT at 100 % during reset (base pull-up), each NTC on its own ADC1 input (no multiplexing),
no SMD part at all (the DevKit brings the 3.3 V regulator, USB and the ESD of its own pins).
DevKit pin map (ESP32-S3-DevKitC-1 v1.0/1.1, header J1 = left, J3 = right):
  GPIO4/5 PWM1/2, GPIO6/7 TACH1/2 (PCNT), GPIO15 bypass, GPIO16 LS, GPIO17 1-Wire, GPIO18 LED,
  GPIO8/9 I2C SDA/SCL, GPIO1/2 NTC1/2 (ADC1_CH0/CH1). Strapping pins 0/3/45/46, USB 19/20, UART 43/44,
  RGB 38/48 and the PSRAM pins 35-37 are left unused.
No manufacturer name on the board (copyright / trademark): the silkscreen says "VA MVHR control board"."""
import os

from schgen import Schematic

PROJECT = "mvhr_ctrl"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", PROJECT)

R_AX = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
C_DISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
CP63 = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
CP8 = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
TO92 = "Package_TO_SOT_THT:TO-92_Inline_Wide"   # 2.54 mm pitch: pad 1.5 / drill 0.8 -> annular 0.30 from the drill
XH3 = "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"
XH4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
SOCK22 = "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical"

sch = Schematic(PROJECT, "MVHR control board - ESP32-S3-DevKitC-1, through-hole", "E",
                comments=("Connects to J10 (34-pin ribbon) of power board 439155, replaces control board 439150",
                          "Through-hole only, hand assembly. Interface proven by the alpha prototype 16.10.2026",
                          "Silkscreen: VA MVHR control board rev E (no manufacturer name)"))
P = sch.part
T = sch.text


def R(ref, val, x, y, a, b, **kw):
    P(ref, "Device:R", val, x, y, {"1": a, "2": b}, footprint=R_AX, **kw)


def C(ref, val, x, y, a, b, fp=C_DISC, **kw):
    P(ref, "Device:C", val, x, y, {"1": a, "2": b}, footprint=fp, **kw)


def CP(ref, val, x, y, plus, minus, fp=CP63, **kw):
    P(ref, "Device:C_Polarized", val, x, y, {"1": plus, "2": minus}, footprint=fp, **kw)


# =====================================================================  J1: ribbon to power board
sch.box(10, 12, 145, 140, "J1 - 34-pin ribbon to power board 439155 (J10)")
J1_NETS = {1: "24V_IN", 2: "24V_IN", 5: "GND", 6: "GND", 7: "GND", 8: "GND",
           10: "FAN1_TACH", 12: "GND", 13: "LSW_5V", 14: "FAN1_PWM", 16: "FAN1_10V",
           18: "FAN2_TACH", 20: "GND", 22: "FAN2_PWM", 24: "FAN2_10V", 26: "BYPASS_OUT",
           28: "GND", 30: "NTC1", 32: "GND", 34: "NTC2"}
P("J1", "Connector_Generic:Conn_02x17_Odd_Even", "IDC 2x17 -> 439155 J10", 60.96, 63.5,
  {str(p): J1_NETS.get(p) for p in range(1, 35)},
  footprint="Connector_IDC:IDC-Header_2x17_P2.54mm_Vertical", props={"MPN": "Box header 2x17 2.54mm"}, stub=5.08)
T("Measured 16.10.2026: 1/2 = 24 V (29 V no load), 3/4 = +5 V (not used).\n"
  "FAN1 (EXTRACT): 10 tacho, 12 motor GND, 14 PWM input (0 V = stop), 16 +10 V.\n"
  "FAN2 (SUPPLY): 18, 20, 22, 24 in the same order. Motor GNDs isolated on 439155 -> tied to GND.\n"
  "13 = LS (ISP814, 5 V pull-up 2k2 on 439155), 26 = bypass relay drive (BC337 base).\n"
  "28/30 = NTC TEMP1 (extract air), 32/34 = NTC TEMP2 (outdoor intake): 28/32 to GND, 30/34 to the ADC.\n"
  "15/17/19/21 = original SHT1x humidity sensor - not used.", 14, 112)

# =====================================================================  Power
sch.box(150, 12, 420, 140, "Power: 24 V -> PTC -> TVS -> TRACO TSR 1-4850WI 5 V -> Schottky -> DevKit 5V pin")
P("F1", "Device:Polyfuse", "RXEF030", 170, 40, {"1": "24V_IN", "2": "+24V"},
  footprint="Fuse:Fuse_BelFuse_0ZRE0033FF_L11.4mm_W3.8mm",
  props={"MPN": "Littelfuse RXEF030 (72 V, hold 0.30 A / trip 0.60 A @ 20 C), alt. Bel Fuse 0ZRE0033FF1A"})
P("D1", "Device:D_TVS", "P6KE47CA", 200, 40, {"1": "+24V", "2": "GND"},
  footprint="Diode_THT:D_DO-15_P10.16mm_Horizontal", props={"MPN": "P6KE47CA (40.2 V standoff, 64.8 V clamp)"})
CP("C1", "10u/100V", 230, 40, "+24V", "GND", CP8, props={"MPN": "Electrolytic 10 uF 100 V, D8 P3.5"})
P("U1", "Converter_DCDC:R-785.0-1.0", "TSR 1-4850WI", 270, 40, {"1": "+24V", "2": "GND", "3": "5V_DCDC"},
  footprint="mvhr_ctrl:TRACO_TSR-1WI_SIP3_CasePins",
  props={"MPN": "TRACO TSR 1-4850WI, straight pins (9-72 V in, 5 V 1 A); case pins 4/5 = mechanical, no net"})
P("D2", "Diode:1N5819", "1N5819", 310, 40, {"1": "+5V", "2": "5V_DCDC"},
  footprint="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal")
CP("C2", "47u/16V", 340, 40, "+5V", "GND")
C("C3", "100n", 370, 40, "+3V3", "GND")
for i, net in enumerate(["+24V", "+5V", "+3V3", "GND"]):
    sch.pwr_flag(net, 165.1 + i * 15.24, 74.93 if net != "GND" else 72.39)   # on the 1.27 mm grid
T("F1 PTC RXEF030: 72 V, hold 0.30 A / trip 0.60 A at 20 C (hold ~0.20 A at 60 C), pitch 5.1 mm; alternative\n"
  "0ZRE0033FF1A (240 V, 0.33/0.74 A) fits the same holes. Both:\n"
  "a SLOW, temperature dependent limiter for a shorted D1/U1, not a fast fuse. Unit draw < 0.2 A from 24 V.\n"
  "D1 P6KE47CA (bidirectional, DO-15): standoff 40.2 V > 29 V, clamp 64.8 V < 72 V TSR max (as SMAJ40A in D1).\n"
  "U1 TRACO TSR 1-4850WI 9-72 V -> 5 V / 1 A, SIP-3 (1 = IN, 2 = GND, 3 = OUT) + 2 case pins, body 12.1x8.6x17.5 mm;\n"
  "no tracks under the converter (TRACO drawing rev. 2026-07-02, review E-01).\n"
  "D2 1N5819: the DevKit must not get 5 V from both the 5V pin and its USB at once (Espressif: 'mutually\n"
  "exclusive') - the diode keeps the USB 5 V out of the TSR. DevKit 5V pin ~4.6 V is enough for its LDO.\n"
  "+3V3 = the DevKit's own 3.3 V regulator (3V3 pins): pull-ups, NTC dividers, I2C / 1-Wire sensors.", 154, 92)

# =====================================================================  DevKit sockets
sch.box(425, 12, 585, 140, "ESP32-S3-DevKitC-1-N8R8 (or N8/N16R8) in 2x 1x22 sockets 8.5 mm, rows 22.86 mm apart")
KJ1 = {1: "+3V3", 2: "+3V3", 4: "PWM1_GPIO", 5: "PWM2_GPIO", 6: "TACH1_GPIO", 7: "TACH2_GPIO",
       8: "BYPASS_GPIO", 9: "LS_IN", 10: "OW", 11: "LED_GPIO", 12: "I2C_SDA", 15: "I2C_SCL", 21: "+5V", 22: "GND"}
KJ1_NAME = ["3V3", "3V3", "RST", "4", "5", "6", "7", "15", "16", "17", "18", "8", "3", "46", "9", "10",
            "11", "12", "13", "14", "5V", "G"]
KJ3 = {1: "GND", 4: "NTC1_ADC", 5: "NTC2_ADC", 21: "GND", 22: "GND"}
KJ3_NAME = ["G", "TX", "RX", "1", "2", "42", "41", "40", "39", "38", "37", "36", "35", "0", "45", "48",
            "47", "21", "20", "19", "G", "G"]
P("J2", "Connector_Generic:Conn_01x22", "DevKit J1 (left)", 470, 72, {str(p): KJ1.get(p) for p in range(1, 23)},
  footprint=SOCK22, props={"MPN": "Female header 1x22 2.54 mm"}, stub=5.08)
P("J3", "Connector_Generic:Conn_01x22", "DevKit J3 (right)", 545, 72, {str(p): KJ3.get(p) for p in range(1, 23)},
  footprint=SOCK22, props={"MPN": "Female header 1x22 2.54 mm"}, stub=5.08)
for i in range(22):
    T(KJ1_NAME[i], 472.5, 44.3 + i * 2.54, 1.0)
    T(KJ3_NAME[i], 547.5, 44.3 + i * 2.54, 1.0)
T("Pin names = GPIO numbers. Unused: strapping 0/3/45/46, USB 19/20, UART0 43/44 (log),\n"
  "RGB LED 38 (v1.1) / 48 (v1.0), 35-37 (octal PSRAM on R8 variants -> N8R8 is fine), RST.\n"
  "N8 is EOL at Espressif (review E-06): order ESP32-S3-DevKitC-1-N8R8 v1.1.", 428, 127)

# =====================================================================  Fans
sch.box(10, 145, 300, 275, "Fans: stop unless a live GPIO says run (stop bias from the motor +10 V), tacho input")
for n, y0 in ((1, 175), (2, 235)):
    o = 20 * n
    T("FAN%d (%s)" % (n, "EXTRACT" if n == 1 else "SUPPLY"), 15, y0 - 20, 1.8, True)
    R("R%d" % o, "4k7", 22, y0, "PWM%d_GPIO" % n, "PWM%d_XB" % n)
    R("R%d" % (o + 5), "10k", 37, y0, "PWM%d_XB" % n, "GND")
    P("Q%d" % (n + 2), "Transistor_BJT:PN2222A", "PN2222A", 52, y0,
      {"1": "GND", "2": "PWM%d_XB" % n, "3": "PWM%d_B" % n}, footprint=TO92,
      props={"MPN": "onsemi PN2222A (TO-92, pins E-B-C = 1-2-3, flat side as on the silkscreen)"})
    R("R%d" % (o + 1), "22k", 70, y0, "FAN%d_10V" % n, "PWM%d_B" % n)  # preorder P2: stop bias from the MOTOR 10 V
    P("Q%d" % n, "Transistor_BJT:PN2222A", "PN2222A", 100, y0,
      {"1": "GND", "2": "PWM%d_B" % n, "3": "FAN%d_PWM" % n}, footprint=TO92,
      props={"MPN": "onsemi PN2222A (TO-92, pins E-B-C = 1-2-3, flat side as on the silkscreen)"})
    R("R%d" % (o + 2), "4k7", 130, y0, "FAN%d_10V" % n, "FAN%d_PWM" % n)
    R("R%d" % (o + 3), "10k", 170, y0, "+3V3", "FAN%d_TACH" % n)
    R("R%d" % (o + 4), "1k", 200, y0, "FAN%d_TACH" % n, "TACH%d_GPIO" % n)
    C("C%d" % (o + 1), "1n", 230, y0, "TACH%d_GPIO" % n, "GND")
T("Q1/Q2 base pull-up 22k from the MOTOR +10 V: Ib 0.42 mA, Ic 2.1 mA (hFE > 5) -> PWM input 0 V -> fan 0 %.\n"
  "Q3/Q4 pull that base low only while the GPIO drives HIGH (4k7, Ib 0.48 mA) -> 4k7 lifts the PWM -> fan runs.\n"
  "Firmware: NON-inverted PWM (GPIO high = run). Reset / high-Z, DevKit unplugged, 3V3 lost or shorted,\n"
  "+5V lost (F1, U1, D2) or ESP unpowered -> Q3/Q4 off (10k to GND) -> fans 0 % as long as the motors have 10 V.\n"
  "No path depends on an unpowered GPIO (preorder review P2).\n"
  "A HUNG program keeps its last PWM: the firmware must keep the ESP32 task watchdog enabled.\n"
  "Tacho: open collector, 1 pulse/rev, 10k pull-up to 3.3 V, 1k + 1n low-pass to the GPIO (PCNT).", 14, 252)

# =====================================================================  Bypass, LS, NTC, LED
sch.box(305, 145, 585, 275, "Bypass, light switch input, two NTCs on their own ADC inputs, status LED")
R("R11", "1k", 330, 170, "BYPASS_GPIO", "BYPASS_OUT")
R("R12", "10k", 365, 170, "BYPASS_OUT", "GND")          # review E-03: relay OFF while the GPIO floats / no DevKit
R("R13", "10k", 330, 200, "LSW_5V", "LS_IN")
R("R14", "22k", 365, 200, "LS_IN", "GND")
C("C13", "100n", 395, 200, "LS_IN", "GND")
R("R15", "10k", 450, 170, "+3V3", "NTC1")
R("R9", "1k", 510, 170, "NTC1", "NTC1_ADC")              # review E-04: series R between the cable and the ADC pin
C("C14", "100n", 540, 170, "NTC1_ADC", "GND")
R("R16", "10k", 450, 200, "+3V3", "NTC2")
R("R10", "1k", 510, 200, "NTC2", "NTC2_ADC")
C("C15", "100n", 540, 200, "NTC2_ADC", "GND")
R("R19", "1k", 450, 235, "LED_GPIO", "LED_A")
P("D3", "Device:LED", "red 3 mm", 480, 235, {"1": "GND", "2": "LED_A"}, footprint="LED_THT:LED_D3.0mm")
T("BYPASS_OUT -> BC337 + relay RL1 on 439155 (230 V damper actuator). GPIO15 is high-Z at reset (no pull on the\n"
  "DevKit): R12 10k holds the BC337 base low -> relay off in reset, bootloader and without the DevKit (E-03).\n"
  "LS: ISP814 pulls 100 Hz pulses low while the light switch is live; 10k/22k -> 3.4 V max.\n"
  "NTC 5k @ 25 C (B ~3950) between J1 28/30 (TEMP1) and 32/34 (TEMP2), 10k pull-up to 3.3 V,\n"
  "each on its own ADC1 channel (GPIO1 / GPIO2): no NTC multiplexing, no CH340 back-feed (alpha issue).\n"
  "Open NTC -> 3.3 V, short -> 0 V: both rejected by the firmware.", 309, 250)

# =====================================================================  1-Wire DS18B20
sch.box(10, 280, 300, 410, "4x DS18B20 on one 1-Wire bus (GPIO17), 4k7 pull-up, 100R per connector")
R("R60", "4k7", 30, 300, "+3V3", "OW")
NAMES = ["OUTDOOR", "SUPPLY", "EXTRACT", "EXHAUST"]
for i, nm in enumerate(NAMES):
    n = i + 1
    x = 70 + i * 55
    R("R%d" % (60 + n), "100", x, 300, "OW", "OW%d_C" % n)
    P("J%d" % (3 + n), "Connector_Generic:Conn_01x03", nm, x + 10, 345,
      {"1": "+3V3", "2": "OW%d_C" % n, "3": "GND"}, footprint=XH3, props={"MPN": "JST B3B-XH-A"})
T("JST-XH 3-pin: 1 = 3V3, 2 = DATA, 3 = GND (same as rev D). Series 100R per connector LIMIT the current into the\n"
  "ESP32 pin clamps; they do not set a safe clamp voltage. No dedicated TVS (review E-04: open decision, depends on\n"
  "the cable lengths - all sensor cables stay inside the unit).", 14, 386)

# =====================================================================  I2C sensors
sch.box(305, 280, 585, 410, "I2C (GPIO8 SDA, GPIO9 SCL): SHT4x humidity (J8), SCD41 CO2 (J9)")
R("R17", "4k7", 330, 300, "+3V3", "I2C_SDA")
R("R18", "4k7", 365, 300, "+3V3", "I2C_SCL")
R("R7", "100", 400, 300, "I2C_SDA_C", "I2C_SDA")        # review E-04: series R between the cables and the GPIOs
R("R8", "100", 430, 300, "I2C_SCL_C", "I2C_SCL")
SENS = {"1": "+3V3", "2": "GND", "3": "I2C_SDA_C", "4": "I2C_SCL_C"}
P("J8", "Connector_Generic:Conn_01x04", "Humidity SHT4x (0x44)", 430, 330, SENS, footprint=XH4,
  props={"MPN": "JST B4B-XH-A"})
P("J9", "Connector_Generic:Conn_01x04", "CO2 SCD41 (0x62)", 500, 330, SENS, footprint=XH4,
  props={"MPN": "JST B4B-XH-A"})
CP("C5", "100u/10V", 540, 330, "+3V3", "GND")
T("JST-XH 4-pin: 1 = 3V3, 2 = GND, 3 = SDA, 4 = SCL (same as rev C/D). R7/R8 100R in series to the GPIOs.\n"
  "C5 next to J9 on the PCB (SCD41 ~200 mA peaks from the DevKit 3.3 V regulator).", 309, 390)
for i in range(4):
    sch.place("H%d" % (i + 1), "Mechanical:MountingHole", "M3", 540 + i * 10, 290,
              footprint="MountingHole:MountingHole_3.2mm_M3", in_bom=False)

os.makedirs(OUT_DIR, exist_ok=True)
sch.save(os.path.join(OUT_DIR, PROJECT + ".kicad_sch"), paper="A2")
print("saved")
