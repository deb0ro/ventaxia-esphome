# Rev E bring-up and measurements

Bring the board up in five steps and go on only when the previous step passed. Insert the ESP and connect the ribbon
cable to the unit only in the step that asks for it.

**Safety:** the power board 439155 in the unit carries 230 V mains. Measure only on the rev E board, and plug or unplug
the ribbon cable only with the unit disconnected from the mains.

Orientation used below: board as in the [assembly map](../hardware/mvhr_ctrl/osazovaci_mapa_revE.png) – J1 at the
top, the DevKit sockets in the middle, the JST connectors at the bottom. "Left" / "right" lead of a part refers to this
view. The upper socket J2 has pin 1 on the right (square pad) and pin 22 on the left; the lower J3 the same.

Expected currents and NTC voltages are estimates from the design; small deviations are not a fault.

## Test points

All points are component leads on the top side.

| Signal | Where to measure | Note |
|---|---|---|
| GND | right lead of C5 or C2, J2 pin 22 | reference |
| 24 V after the fuse | C1 left (+) | input of U1 |
| 5 V from the converter | D2 right lead | before the Schottky diode |
| +5V for the ESP | D2 left (band), C2 left, J2 pin 21 | after the diode |
| +3V3 | C5 left, C3 left, J2 pins 1–2 | only with the ESP inserted |
| FAN1 (extract) +10 V | R21 left, R22 left | only with the unit |
| FAN1 PWM | Q1 right lead (C), R22 right | to J1 pin 14 |
| FAN2 (supply) +10 V | R41 left, R42 left | only with the unit |
| FAN2 PWM | Q2 right lead (C), R42 right | to J1 pin 22 |
| FAN1 / FAN2 tacho | R24 left / R44 left | GPIO6 / GPIO7 on the right lead |
| NTC1 / NTC2 | R9 left / R10 left | ADC GPIO1 / GPIO2 on the right lead |
| Light switch (LS) | R14 left | GPIO16 |
| Bypass | R12 left | GPIO15 on R11 left |
| 1-Wire / SDA / SCL | R60 / R17 / R18 right | GPIO17 / 8 / 9 |

## Step 1 – visual check

- [ ] No solder bridges between the pins of J1 (2×17) and the sockets J2/J3
- [ ] All joints shiny and conical, no pin left unsoldered
- [ ] C1, C2, C5: + on the left (square pad), negative stripe on the right
- [ ] D2: band on the left. D3: cathode (shorter lead, flat side) on the left
- [ ] Q1–Q4: flat side down, transistors not swapped
- [ ] U1: pin 1 (+Vin) on the left, printed side down
- [ ] J1: key notch down, towards the inside of the board
- [ ] Resistor values as on the map, especially 22k (R14, R21, R41) and 4k7 around Q3/Q4
- [ ] Leads trimmed, nothing sticking out more than ~2 mm

## Step 2 – resistance without power

No ESP, no cable, no power. The main point: no short between the supply rails. Capacitors charge from the meter, so
high values slowly rise – that is fine.

| Between | Expected |
|---|---|
| J1 pin 1 ↔ C1 left (fuse F1) | below 2 Ω |
| C1 left (24 V) ↔ GND | above 10 kΩ, never below 1 kΩ |
| J2 pin 21 (+5V) ↔ GND | above 1 kΩ |
| C5 left (+3V3) ↔ GND | above 100 kΩ |
| +5V ↔ +3V3 | above 100 kΩ |
| 24 V ↔ +5V | above 100 kΩ |
| D2 in diode mode, red probe on the right | 0.2–0.4 V, reverse OL |
| R9 right ↔ +3V3 (NTC1) | 11 kΩ |
| R10 right ↔ +3V3 (NTC2) | 11 kΩ |
| R24 right ↔ +3V3 (tacho 1) | 11 kΩ |
| R44 right ↔ +3V3 (tacho 2) | 11 kΩ |
| R17 right, R18 right, R60 right ↔ +3V3 | 4.7 kΩ each |
| R11 left ↔ GND (bypass) | 11 kΩ |
| R14 left ↔ GND (LS) | 22 kΩ |
| R20 left, R40 left ↔ GND (PWM) | 5–15 kΩ each, depending on the meter |

## Step 3 – 24 V without the ESP

Feed 24 V into J1 pins 1/2 (+) and pins 5–8 (−) from a bench supply limited to 200 mA. Without a bench supply skip to
step 5 part A, which is also done without the ESP.

| What | Where | Expected |
|---|---|---|
| Supply current | bench supply | below 20 mA |
| 24 V after the fuse | C1 left | as the supply, at most 0.1 V lower |
| Converter output | D2 right | 4.9–5.1 V |
| +5V for the ESP | J2 pin 21 | 4.6–5.0 V |
| +3V3 | C5 left | 0 V – without the ESP there is no 3V3 source |

- [ ] After one minute U1, F1 and D1 are not warm
- [ ] J2 pin 21 is not above 5.3 V – otherwise do not insert the ESP

## Step 4 – with the ESP

Flash the firmware over USB with the ESP outside the board. Then switch off, insert the ESP with the antenna to the
right and switch on again.

| What | Where | Expected |
|---|---|---|
| Supply current | bench supply | 20–50 mA, short peaks up to 100 mA |
| +5V for the ESP | J2 pin 21 | 4.5–4.9 V |
| +3V3 with Wi-Fi running | C5 left | 3.2–3.4 V |
| Bypass idle | R12 left | 0 V |
| LS idle | R14 left | 0 V |
| NTC without a sensor | R9 right, R10 right | about 3.3 V |
| 1-Wire, SDA, SCL | R60, R17, R18 right | about 3.3 V |

- [ ] The ESP joins Wi-Fi and its web page opens (user `admin`, password from `secrets.yaml`)
- [ ] The clock is correct (SNTP) and the log shows no reboots
- [ ] +3V3 does not drop below 3.2 V while the web page loads

Without the unit it is normal that the firmware reports fan faults, the temperatures are unknown, the I²C sensors are
missing and LED D3 blinks.

## Step 5 – in the unit

First confirm without the ESP that the fans stay stopped – the main safety property of the board. Only then insert
the ESP.

### Part A: without the ESP

Unplug the unit from the mains, remove the old control board, take the ESP out of the sockets and connect the ribbon
cable to J10 of the 439155 (pin 1 to pin 1). Then plug the unit in.

| What | Where | Expected |
|---|---|---|
| 24 V input | C1 left | 24–29 V |
| +5V for the ESP | J2 pin 21 | 4.6–5.0 V |
| FAN1 +10 V | R21 left | about 10 V |
| FAN2 +10 V | R41 left | about 10 V |
| FAN1 PWM | Q1 right | below 0.3 V |
| FAN2 PWM | Q2 right | below 0.3 V |

- [ ] Both fans stand still

If a fan runs or a PWM line is high, unplug the unit at once and look for the fault.

### Part B: with the ESP

Unplug the unit, insert the ESP and plug the unit in again. On the web page switch Mode to Manual (it ends by itself
after 2 hours).

| What | How | Expected |
|---|---|---|
| Manual supply 0 % | Q2 right | below 0.3 V, supply fan stopped |
| Manual supply 50 % | Q2 right | about 5 V (PWM average) |
| Manual supply 100 % | Q2 right | about 10 V |
| Manual extract 0 % | Q1 right | below 0.3 V, extract fan stopped |
| Manual extract 50 % | Q1 right | about 5 V |
| Manual extract 100 % | Q1 right | about 10 V |
| Fan speeds | Extract / Supply fan speed on the web page | about 1300 rpm at 50 %, extract and supply not swapped |
| NTC1 extract | R9 left + temperature on the web page | about 1.5–2.2 V, house temperature |
| NTC2 outdoor | R10 left + temperature on the web page | about 1.5–2.8 V, outdoor temperature |
| Light switch | switch the light on + Light switch on the web page | changes to On |
| Bypass | Manual bypass + R12 left | relay clicks, about 3 V |

- [ ] Back in Auto the fans ramp smoothly to their levels and no fault is reported
- [ ] After 30 minutes of operation nothing on the board is hot
