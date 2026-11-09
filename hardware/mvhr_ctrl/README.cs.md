# Rev E – VA MVHR control board

Rev E je řídicí deska jen s vývodovými součástkami, osazuje se doma. Výpočetní modul je ESP32-S3-DevKitC-1 zasunutý ve dvou paticích.

Deska se připojuje 34žilovým plochým kabelem do J10 výkonové desky 439155 a nahrazuje řídicí desku 439150. Nemá displej ani tlačítka, ovládá se z Home Assistantu.

Na desce není jméno výrobce jednotky. Potisk zní „VA MVHR control board rev E“.

**Rozměr 95 × 95 mm** (od 17. 10. 2026, dřív 95 × 66 mm). **Výroba: JLCPCB**, holé desky, osazení doma. Deska splňuje i standard Gatemy (kapitola níže).

## Soubory

| Soubor | Obsah |
|---|---|
| `mvhr_ctrl.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, `mvhr_ctrl.pretty/`, `fp-lib-table` | Projekt KiCad 10, vygenerovaný skripty v `../tools`. Vlastní pouzdro pro TRACO TSR 1WI. |
| `mvhr_ctrl_schematic.pdf` | Schéma |
| `mvhr_ctrl_assembly.pdf` | **Osazovací výkres**: reference a hodnoty (F.Fab), potisk, obrys |
| `fab/mvhr_ctrl_jlcpcb.zip` | **Data pro JLCPCB**: Gerber X2 + Excellon PTH/NPTH |
| `fab/mvhr_ctrl_odb.zip`, `fab/mvhr_ctrl_pool.zip`, `fab/gerber/` | ODB++, Gatema POOL (`.top .bot .smt .smb .plt .pth .mill .dim`), jednotlivé Gerbery |
| `mvhr_ctrl_bom.csv` | Součástky nosné desky (z netlistu) |
| `nakup_revE.csv` | **Nákupní seznam**: BOM + DevKit, patice, protikusy konektorů a kabely (review E-06) |
| `render_top.png`, `render_bottom.png` | 3D náhled |
| `drc.rpt`, `erc.rpt` | ERC 0, DRC 0 chyb, 0 nepropojených plošek |

DRC hlásí jen `lib_footprint_mismatch`. Je to záměr: čáry potisku jsou zesílené na 0,15 mm.

**Přegenerování:**

```
python ../tools/make_fp_tsr1wi.py
python ../tools/build_sch_e.py
python ../tools/route_e_until_clean.py
python ../tools/export_fab_e.py
```

`route_e_until_clean.py` pouští generátor desky a routování Freeroutingem tak dlouho, dokud DRC nehlásí 0 chyb a 0 nepropojených plošek. Freerouting není deterministický.

## JLCPCB (stránka Capabilities, 17. 10. 2026)

| Parametr | JLCPCB, 2 vrstvy | Rev E |
|---|---|---|
| Spoj / mezera | ≥ 0,10 / 0,10 mm | spoje 0,25–0,6 mm, u plošek nejméně 0,15 mm (dva krátké úseky NTC1), mezery 0,20 mm |
| Prokov | otvor ≥ 0,15 mm, okruží ≥ 0,18 mm (doporučeno 0,25) | **0,9/0,4 mm = 0,25 mm** (na desce 95 × 66 mm se nedaly odroutovat, na 95 × 95 mm ano) |
| Okruží THT | – | plošky nejméně 0,25 mm (U1 vývody 1–3: 1,5/0,8 mm; jazýčky krytu: prokovené drážky 1,3 × 5,0 mm, ploška 2,1 × 5,8 mm) |
| Otvor–otvor | plošky 0,45 mm, prokovy 0,2 mm | splněno, nejbližší u U1: 2,1 mm |
| Měď od hrany | ≥ 0,2 mm | 0,5 mm |
| NPTH | ≥ 0,5 mm | 4× 3,2 mm (M3) |
| Maska | 1:1 (expanzi dělá CAM JLC), můstek ≥ 0,10 mm | 1:1, mezery mezi ploškami ≥ 0,8 mm |
| Potisk | čára ≥ 0,15 mm, text ≥ 1,0 mm | 0,15 mm, text 1,2 mm |
| Tloušťka | 0,4 / 0,6 / 0,8 / 1,0 / 1,2 / **1,6** / 2,0 mm | **1,6 mm** (v datech a ve skladbě desky) |

**Objednávka JLCPCB:**
- Nahrát `fab/mvhr_ctrl_jlcpcb.zip`.
- Parametry: 2 vrstvy, 95 × 95 mm, 5 ks, FR-4, 1,6 mm, 1 oz, HASL lead-free, zelená maska, bílý potisk, bez osazení.
- Gerber job (`gbrjob`) má revizi E, tloušťku 1,6 mm a povrch HAL lead-free.

## Gatema (alternativa)

- **Standard Gatemy:** pro ni nastavit v `build_pcb_e.py` `MASK_EXPANSION = 0.05` a `BOARD_THICKNESS = 1.5`.
- **Okruží:** Gatema ho počítá od vrtáku (výsledný otvor + 0,1 mm). Nejmenší okruží je u prokovů 0,15 mm.
- **POOL servis:** krok 1 „2V Cu 18/18 µm, 1,5 mm, LF HAL, 2x zelená NM, 1x bílý potisk“, 5 ks, 379 otvorů (375 PTH včetně prokovů a 2 drážek, 4 NPTH). Cena se ukáže až po vyplnění kontaktních údajů. Aktuální export je nastavený pro JLCPCB, pro Gatemu ho znovu vygenerovat s jejími konstantami.
- **Data:** `fab/mvhr_ctrl_pool.zip`. Do objednávky napsat, že průměry otvorů jsou výsledné.

## Zapojení DevKitu (ESP32-S3-DevKitC-1-N8R8 v1.1)

| GPIO | Funkce | GPIO | Funkce |
|---|---|---|---|
| 4 | PWM odtah (FAN1), **neinvertovaný** (1 = běží) | 1 | NTC1 TEMP1 odtah, ADC1_CH0 (přes R9 1k) |
| 5 | PWM přívod (FAN2), **neinvertovaný** (1 = běží) | 2 | NTC2 TEMP2 venku, ADC1_CH1 (přes R10 1k) |
| 6 | tacho odtah (PCNT) | 8 / 9 | I²C SDA / SCL (přes R7/R8 100R na J8, J9) |
| 7 | tacho přívod (PCNT) | 17 | 1-Wire (4× DS18B20, J4–J7) |
| 15 | bypass (R11 1k, pull-down R12 10k) | 18 | LED D3 (aktivní v 1) |
| 16 | vstup LS (vypínač světla) | 5V / 3V3 | napájení z TSR přes 1N5819 / 3,3 V z DevKitu |

**Varianta N8 je u Espressifu EOL** (review E-06). Varianty N8R8 a N16R8 vyhovují, protože GPIO35–37, které obsadí octal PSRAM, nepoužíváme.

Nepoužité piny:
- **strapping:** 0, 3, 45, 46;
- **USB:** 19, 20;
- **UART log:** 43, 44;
- **RGB LED:** 38 (v1.1) a 48 (v1.0);
- **octal PSRAM:** 35–37.

## Chování v poruchových stavech (review E-02, E-03, preorder P2)

Budič od 18. 10. 2026: báze Q1/Q2 má pull-up 22k z **+10 V motoru** (FAN1_10V/FAN2_10V), takže ventilátor je ve výchozím stavu zastavený vždy, když má motor napájení. Rozběhnout ho může jen **Q3/Q4**, který bázi Q1/Q2 stáhne k zemi, a to jen když živé GPIO dává 1 (R20/R40 4k7, R25/R45 10k k GND). Proudy: báze Q1/Q2 0,42 mA, kolektor 2,1 mA (stačí hFE > 5), báze Q3/Q4 0,48 mA.

| Stav | Ventilátory | Bypass |
|---|---|---|
| Reset, bootloader, flash (GPIO ve vysoké impedanci) | stojí: Q3/Q4 vypnuté (10k k GND), Q1/Q2 sepnuté z 10 V motoru | relé vypnuté, R12 drží bázi BC337 dole |
| DevKit vytažený, 3V3 zanikne nebo ho zkratuje čidlo, ESP bez napájení | stojí, žádná cesta nezávisí na chování nenapájeného GPIO | vypnuté |
| Výpadek +5V jen na naší desce (F1, U1, D2) při živých 10 V motorů | stojí | vypnuté |
| Zamrzlý program | zůstane poslední PWM. **Firmware musí mít zapnutý task watchdog ESP32.** | poslední stav |
| Výpadek pomocného 10 V výstupu motoru | R22/R42 nemají čím přitáhnout PWM nahoru, vstup motoru drží jeho vnitřní pull-down (podle měření na alfě) | – |

Zamrzlý program držící GPIO v 1 nechá ventilátory běžet, proto firmware musí mít task watchdog.

Ověřit osciloskopem na sestavené desce (oba kanály při 0/25/50/100 %, šířky pulzů a nízkou úroveň; dva saturované BJT přidávají zpoždění, frekvence PWM 1 kHz jako na alfě): PWM výstup při zapnutí, resetu, vytaženém DevKitu, zkratu 3V3 na GND a odpojeném +5V (vytažená D2) při živé jednotce.

## Hlavní rozdíly proti rev D1 a alfě

- **Žádné SMD:**
  - LoLin a AP2112 odpadly;
  - P6KE47CA v pouzdře DO-15;
  - tranzistory PN2222A v pouzdře TO-92 s roztečí 2,54 mm.
- **U1 TRACO TSR 1-4850WI** má vlastní pouzdro podle výkresu TRACO z 2. 7. 2026 (review E-01):
  - vývody 1–3 a mechanické vývody krytu 4/5 bez sítě;
  - tělo 12,1 × 8,6 × 17,5 mm;
  - pod tělem zakázané spoje i prokovy, kromě dvou koridorů pro vývody 1 a 3.
- **Každé NTC má vlastní vstup ADC1** a sériový odpor 1k.
- **I²C přes 100R**, 1-Wire přes 100R na každý konektor, tacho přes 1k, LS přes 10k (review E-04).
- **F1 Littelfuse RXEF030** (72 V, hold 0,30 A / trip 0,60 A při 20 °C, při 60 °C hold asi 0,20 A). Alternativa Bel Fuse 0ZRE0033FF1A (240 V, 0,33/0,74 A) sedí do stejných otvorů (rozteč 5,1 mm), u Farnellu má ale dodací lhůtu 13 týdnů. Je to pomalý omezovač při poruše D1 nebo U1, ne rychlá pojistka.
- **Všechny vývody THT mají tepelné můstky**, takže se snáz pájejí a odpájejí (review E-09).

## Osazení

- Řiďte se `mvhr_ctrl_assembly.pdf` (reference a hodnoty). Reference na potisku jsou nad díly, po osazení zůstávají čitelné.
- Pájet od nejnižších dílů:
  1. odpory (rozteč 7,62 mm);
  2. diody;
  3. keramické kondenzátory;
  4. TO-92;
  5. elektrolyty;
  6. konektory;
  7. patice a U1.
- **Pod DevKitem není žádná součástka.** Obvody ventilátorů (R21–R24, R41–R44, Q1, Q2, C21, C41) jsou pod spodní řadou patic, spínače Q3/Q4 s R20/R25/R40/R45 vlevo od ní. Výška dílů není omezená.
- **TO-92:** PN2222A má vývody E-B-C. Plochá strana je podle potisku, krajní vývody se roztáhnou na 2,54 mm.
- **U1:** jazýčky krytu 4/5 (0,6 × 2,0 mm, o 1,1 mm mimo řadu vývodů) jdou do oválných drážek, ty jsou záměrně delší na obě strany. Zapájet je. Elektricky nejsou nikam připojené. Před objednáním desky přiložit skutečný TSR na výtisk 1:1 (`mvhr_ctrl_assembly.pdf`).
- **Pod anténou modulu** je pravý konec mezi paticemi. Je tam záměrně bez mědi a bez součástek.
- **Polarita:** C1, C2, C5 mají + u čtverhranné plošky. D2 a LED mají katodu („K“, resp. kratší vývod). D1 je obousměrná.
- **Oživení:**
  1. Bez DevKitu na proudově omezeném zdroji 24 V změřit +5 V na C2 (asi 4,6 V).
  2. Ověřit, že relé bypassu nesepne.
  3. Teprve potom zasunout DevKit.

## Otevřené body z review E

- **E-04, ochrana kabelů:** sériové odpory omezují proud, ale nedávají bezpečné svorkové napětí. Pokud budou kabely čidel dlouhé nebo povedou mimo jednotku, doplnit TVS nebo diodové svorky u konektorů.
- **E-05, odběr ze 3V3:** všechna čidla napájí 3V3 DevKitu (SGM2212, 800 mA). Ve špičce je to 545 mA (SCD41 205 mA a Wi-Fi 340 mA). Na sestavené desce změřit 5V a 3V3 u SCD41 a teplotu regulátoru. Případně doplnit samostatný stabilizátor pro čidla.
- **E-07:** schéma je zatím kreslené přes názvy sítí, místní obvody chce review nakreslit dráty.
- **Mechanika:** středy otvorů M3 mají rozteč 88 × 88 mm. Ověřit proti držáku v jednotce, včetně ohybů kabelů a výšky U1 (17,5 mm).
- **Firmware pro rev E:**
  - nové piny, dva ADC, PCNT a NVS; PWM **neinvertované**;
  - zachovat řízení bez HA, priority ochran, poruchy ventilátorů, stáří dat čidel a task watchdog.
