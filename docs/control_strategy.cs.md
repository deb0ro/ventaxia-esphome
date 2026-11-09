# Jak řídit rekuperaci – podklad pro automatizaci v HA

Stav 16. 10. 2026. Vychází z originálního manuálu Sentinel Kinetic (Installation & Commissioning, Vent-Axia 2009), obecných zásad pro řízené větrání s rekuperací a z dat alfa prototypu v HA.

## 1. Jak jednotka funguje

```
venku ──► sání (TEMP2) ──► [výměník] ──► přívod do obytných místností
                                 ▲
dům (kuchyň, koupelna, WC) ──► odtah (TEMP1) ──► [výměník] ──► výfuk ven
```

- Dva ventilátory, dvě oddělené cesty. Výměník předá teplo z odpadního vzduchu čerstvému, vzduch se nemísí (účinnost až ~90 %).
- **Přívod** jde do obytných místností a ložnic, **odtah** z kuchyně, koupelen a WC. Vzduch proudí přes dům od „čistých“ místností k „mokrým“.
- **Bypass** (klapka, relé na J10 pin 26) pustí venkovní vzduch mimo výměník. Slouží k letnímu nočnímu chlazení.
- **Čidla jednotky:**
  - TEMP2 = venkovní vzduch na sání, v manuálu „T1 supply“.
  - TEMP1 = vzduch odsávaný z domu, v manuálu „T2 extract“. Je to nejlepší dostupné měřítko teploty v domě.
  - Teplotu přívodu do domu ani výfuku ven jednotka neměří. Doplní je revize D (čtyři DS18B20).

## 2. Stejné otáčky, nebo přetlak a podtlak?

**Základ je rovnotlak: přívod = odtah v m³/h, ne v procentech.** Potrubí přívodu a odtahu má jiný odpor, takže stejné procento PWM nedává stejný průtok. Proto se jednotka při instalaci „zaregulovává“ a v manuálu má zvlášť nastavení *Supply* a *Extract* pro každý stupeň.

| Režim | Kdy | Proč |
|---|---|---|
| **Rovnotlak** (přívod = odtah) | Normálně, celý rok | Rekuperace funguje jen na vzduch, který jde výměníkem. Při nerovnováze se rozdíl dorovná netěsnostmi bez rekuperace. |
| **Mírný podtlak** (odtah o 5–10 % víc) | Zimní kompromis, vlhké domy | Vlhký teplý vzduch se nevtlačuje do konstrukce (stěny, strop), kde by kondenzoval. Doporučované pro naše klima. |
| **Přetlak** (přívod > odtah) | Spíš nikdy v zimě | Tlačí vlhkost do konstrukce a hrozí kondenzace a plíseň. Krátkodobě v létě nevadí. |
| **Silný podtlak** (sníží se přívod) | Jen ochrana proti zamrznutí | Viz níže. V domě s kotlem nebo krbem na komínový tah může podtlak obrátit tah spalin. |

**Výchozí hodnoty Vent-Axia** (procenta průtoku, ne našeho PWM):

| Stupeň | Přívod / odtah |
|---|---|
| Low | 20 % |
| Normal | 30 % |
| Boost | 50 % |
| Purge | 100 % |
| Odsavač nad sporákem | přívod 30 % / odtah 100 % |

**Co z toho plyne pro nás:**
- Naše procenta jsou procenta PWM, ne průtoku, takže se s tabulkou nedají přímo srovnat. Teď obě větve jedou na 55 % PWM a točí ~1 390 ot/min (FAN1) a ~1 410 ot/min (FAN2). Na 100 % je to 2 346 a 2 172 ot/min.
- Původní nastavení technika bylo uložené v desce 439150. Než ji odložíš, stálo by za to ji krátce připojit a opsat z displeje nastavení *Commissioning*: Low, Normal a Boost pro Supply i Extract. To je zaregulování přímo pro tvůj dům.
- **Ověřeno 16. 10.: FAN1 = odtah (fialový J7), FAN2 = přívod (modrý J6).** Se zvýšením otáček FAN2 víc foukala přívodní vyúsť ve stropě. Na 100 % točí odtah 2 346 a přívod 2 172 ot/min.

**Kolik vzduchu:**
- Orientačně 25–30 m³/h na osobu, nebo ~0,3–0,5 výměny objemu domu za hodinu.
- Při sprchování a vaření krátce víc (boost), v noci a při nepřítomnosti méně (low), ale nikdy úplně vypnout.

## 3. Teplota

### Letní bypass (podle manuálu)

| Parametr | Výchozí hodnota | Rozsah |
|---|---|---|
| **Indoor Temp** – požadovaná teplota v domě | 25 °C (jinde 21 °C) | 16–40 °C |
| **Outdoor Temp** – minimální venkovní teplota pro bypass | 14 °C | 5–20 °C |

- Doporučení manuálu: Indoor Temp nastavit **3 °C nad teplotu topení**.
- Bypass se otevře, když:
  - je **dům teplejší než požadovaná teplota**,
  - **venku je chladněji než uvnitř**,
  - **a zároveň venku není pod minimem**, aby netáhlo.
- Návrh pro HA:
  - **otevřít**, když TEMP1 > 24 °C **a** TEMP2 < TEMP1 − 2 °C **a** TEMP2 > 14 °C;
  - **zavřít**, když TEMP1 < 22 °C **nebo** TEMP2 > TEMP1 − 1 °C **nebo** TEMP2 < 13 °C (hystereze, ať klapka necvaká).
  - Při otevřeném bypassu v noci zvednout otáčky, aby dům víc vychladl.
  - **Když je venku tepleji než uvnitř**, nechat bypass zavřený a jet spíš na low. Výměník pak drží chlad v domě.

### Ochrana proti zamrznutí výměníku (podle manuálu, výchozí „Airflow Mode“)

- **Sání 0 až −20 °C:** sníží se přívod a zvýší se odtah. Teplý odpadní vzduch rozmrazuje výměník. Přívod se může cyklicky zastavovat (15 min stojí, 45 min běží) podle toho, jak je pod nulou.
- **Sání pod −20 °C:** přívod stojí, odtah běží sníženě.
- Alternativa „Bypass Mode“ otevře pod 0 °C bypass místo snižování přívodu. Nevytváří podtlak, ale do domu jde studený vzduch.
- **Pokoj pod 5 °C** (porucha topení): jednotka se zastaví a každou hodinu krátce zkusí změřit teplotu („Room Too Cold“).

**Pro nás:**
- Mráz hrozí na straně výfuku, tam kondenzuje vlhkost z domu. Rozhoduje tedy teplota vzduchu za výměníkem, ne venku.
- Do revize D proto patří DS18B20 do výfuku a automatizace má hlídat hlavně ji: pod ~1 °C snížit přívod.
- Do té doby je náhradou TEMP2 (sání) s prahy podle manuálu.
- ⚠️ Máš v domě kotel nebo krb s komínovým tahem? Pokud ano, podtlakový režim je potřeba omezit.

### Ostatní

- **Vlhkost** (SHT4x v revizi D): boost nad 70 % RV nebo při prudkém nárůstu (sprcha), návrat pod 60 %.
  - V zimě větrání vysušuje. Při RV pod ~30 % stáhnout na low.
- **CO₂** (SCD41 v revizi D): Normal při 1 000 ppm, Boost při 2 000 ppm (výchozí hodnoty Vent-Axia). Pro pohodu je lepší cílit pod ~1 000 ppm v ložnici.
- **Teplotní boost** v manuálu: Normal 17 °C, Boost 27 °C (vstup proporcionálního čidla).
- **Vypínač světla (LS):** zpoždění 0 min, doběh 15 min (rozsah 0–25 min). V našem zapojení nevyužité.
- **Filtry:** výchozí interval 12 měsíců, první půlrok kontrolovat měsíčně.

## 4. Co ukazují data z alfy

- **Teploty kolísají až o ±1,5 °C mezi měřeními** (TEMP1 24,4–28,2 °C během pár minut).
  - Pro automatizace jsou potřeba vyhlazené hodnoty: medián nebo klouzavý průměr ve firmwaru, případně helper „Statistics“ v HA.
  - Kalibrace NTC (B = 3950 je jen odhad) je pořád otevřená.
- TEMP2 (sání) ukazuje 19–22 °C. Na říjnové poledne venku je to podezřele hodně. Buď je v tom kalibrace, nebo čidlo ohřívá teplé okolí jednotky, nebo stojí ventilátory. Ověřit proti venkovnímu teploměru.
- Tachometry fungují. Jako detekci poruchy lze hlídat „ventilátor má běžet, ale otáčky jsou 0 déle než 1 minutu“.

## 5. Řízení běží na ESP, HA je jen ovladač

Rozhodnutí 16. 10.: logika je ve firmwaru [ventaxia_alpha.yaml](firmware/ventaxia_alpha.yaml), aby jednotka fungovala i bez HA nebo Wi-Fi. Parametry jsou entity ESPHome uložené ve flash, takže přežijí výpadek proudu i HA.

| Entita v HA | Co dělá |
|---|---|
| **Mode** | Auto, Low, Normal, Boost, Manual. Auto = Normal; v revizi D přibude řízení podle CO₂ a vlhkosti. |
| **Boost** / **Boost cancel** | Boost na „Boost duration“ (výchozí 30 min), pak návrat do režimu |
| **Low / Normal / Boost supply %, extract %** | PWM pro každý stupeň zvlášť. Výchozí odtah o 5 % víc než přívod (mírný podtlak): 35/40, 50/55, 75/80. |
| **Manual supply % / extract %**, **Manual bypass** | Platí jen v režimu Manual |
| **Summer bypass** (zap/vyp), **Bypass comfort temperature** (24 °C), **Bypass outdoor minimum** (14 °C) | Letní bypass podle kapitoly 3 |
| **Frost protection mode** (Airflow / Bypass), **Frost protection start** (0 °C) | Ochrana proti mrazu podle manuálu Vent-Axia. Režim Bypass nevytváří podtlak (vhodný při kotli nebo krbu s komínovým tahem). |
| **Night mode** (zap/vyp), **Night start** (22:00), **Night end** (08:00), **Night supply % / extract %** (40/40) | V režimu Auto v nastaveném čase jede jednotka na noční procenta. Čas bere ESP z internetu (SNTP), takže noční režim funguje i bez HA. Boost a digestoř mají přednost. |
| **Cooker hood** (zap/vyp), **Cooker hood supply %** (60), **Cooker hood extract %** (0) | Při běžící digestoři jen přívod jako náhradní vzduch, odtah stojí (menší podtlak, kamna netáhnou kouř). Zapíná a vypíná ho automatizace HA podle příkonu digestoře (> 50 W 15 s / < 50 W 3 min). Když HA nepošle „vypnout“, ESP režim samo ukončí po 2 h. |
| **Holiday** (zap/vyp), **Holiday supply % / extract %** (25/30) | Dovolená: minimální větrání místo Auto/Low/Normal i nočního režimu. Přepíná ho automatizace HA podle `input_boolean.dovolena`; stav ESP drží i po restartu. Boost a digestoř mají přednost, mráz, bypass, volné chlazení a „Room too cold“ platí dál. |
| **Night start / end weekend** (23:00 / 09:00), **Weekend night times** (zap) | V pátek a sobotu večer začíná noc v „weekend“ čase, v sobotu a neděli ráno v něm končí |
| **Dry air protection** (zap), **Humidity minimum** (35 %) | Ochrana proti vysušení: když medián vlhkosti v domě (`sensor.dum_vlhkost_median_zigbee` z HA) klesne pod minimum, Auto jede nejvýš na Low. Vypne se nad minimem + 3 %. Bez spojení s HA se nepoužije. Stav **Dry air protection active**. |
| **Free cooling** (zap), **Free cooling supply / extract %** (60/60) | Noční chlazení v létě: při otevřeném letním bypassu v Auto, a když je venku aspoň o 3 °C chladněji než v domě, jedou ventilátory aspoň na tato procenta |
| **Fireplace** / **Fireplace cancel**, **Fireplace supply / extract %** (60/30), **Fireplace duration** (15 min) | Krbový režim: krátký přetlak na zatopení. Přebíjí stupně i dovolenou, digestoř má přednost. |
| **Airing 1/2/3 time** (08:00 / 12:00 / 19:00), **Airing N enabled**, **Airing duration** (30 min), **Airing supply / extract %** (100/100) | Plánované provětrání domu třikrát denně. Platí v Auto, ne o dovolené a ne během Boostu. Má přednost před nocí, krb a digestoř mají přednost před ním. Ochrany (mráz, studený dům, porucha ventilátoru) platí dál, strop kvůli suchému vzduchu ne. |
| **Fan ramp rate** (2 %/s) | Plynulá změna otáček při přepínání režimů a měkký rozběh po startu (0 → 55 % za ~28 s) |
| **Filter replaced**, **Filter change interval** (180 d), **Filter clog alarm** (15 %) | Stáří filtru podle data (SNTP), motohodiny a odhad zanesení: prvních 72 h chodu se učí otáčky s čistým filtrem pro každý krok 5 % PWM (krok, který se objeví až později, se doučí za 10 min, nejpozději do 720 h), pak se hlídá odchylka. Stavy **Filter state**, **Filter change needed**, **Filter age / days left**, **Extract/Supply filter rpm deviation**. Zda otáčky se zanesením rostou, nebo klesají, zatím není ověřené. |
| **Control state** | Text, co jednotka právě dělá a proč (např. „Auto: Normal, frost: supply 75 %“) |
| **Supply / Extract fan level** | Cílové PWM % (skutečné se k němu blíží rampou) |
| **Bypass open, Frost protection, Room too cold, Extract/Supply fan fault** | Stavy pro dashboard a notifikace |

Pro HA zbývá jen to, co nemusí běžet při jeho výpadku:
- přepínání Holiday podle `input_boolean.dovolena`,
- `fan.rekuperace` (šablonový ventilátor): 33 % = Low, 67 % = Normal, 100 % = Boost, zapnout = Auto, vypnout = Manual 0/0; procenta ukazují vyšší z obou ventilátorů,
- statistiky: bypass otevřený dnes (h), počet otevření bypassu dnes, ochrana proti mrazu dnes (h), Boost dnes (h), energie dnes / měsíc ze zásuvky,
- `sensor.dum_vlhkost_median_zigbee`: medián vlhkosti místností (bez koupelny a technické místnosti) pro ochranu proti vysušení,
- notifikace o poruše ventilátoru a o filtru,
- dashboard.

Teploty se vyhlazují mediánem z 5 měření přímo ve firmwaru.

**Oprava po code review (17. 10.):**

Firmware se generuje skriptem [gen/gen_fw.py](firmware/gen/gen_fw.py) ze šablony [gen/fw_template.yaml](firmware/gen/fw_template.yaml). Upravuje se šablona a tabulka v generátoru, ne výsledný YAML.

- **Ukládání nastavení:** ESP8266 má na uložená nastavení jen 512 B a dřív se nevešla. Všechna nastavení, data filtru a reference otáček jsou teď v jednom verzovaném záznamu `cfg` (128 B). Entity se při startu načtou z něj a každá změna se do něj zapíše. Nová nastavení dostanou volné pozice 82–127, takže další flash už nic nevynuluje.
- **Pořadí řízení:** nejdřív požadavek (režim, noc, dovolená, krb, letní bypass a chlazení, digestoř), potom ochrany ve všech režimech včetně Manual: start, studený dům, suchý vzduch, mráz, porucha ventilátoru. Pozdější větev už ochranu nezruší. Při mrazu v režimu Bypass zůstává bypass otevřený i s digestoří.
- **Manual** po restartu nepřetrvá (vrátí se Auto) a sám skončí po 2 h. Vypnutí `fan.rekuperace` tedy zastaví ventilátory na 2 h.
- **Venkovní teplota:**
  - platí jen čerstvé surové měření TEMP2 (do 2 min);
  - jinak se použije meteostanice z HA (do 30 min);
  - když chybí obojí, nastoupí bezpečný režim proti mrazu: Bypass otevře bypass a jede na Low, Airflow sníží přívod na polovinu Low;
  - nový stav **Temperature sensor fault**.
- **Porucha ventilátoru (3. review):**
  - Ventilátor s výkonem nad 20 %, který 60 s nedává platné otáčky, má poruchu. Ta trvá, i když ochrana výkon sníží.
  - Druhý ventilátor se zastaví **okamžitě**, bez komfortní rampy (pevné pravidlo, nezávislé na nastavení Low). Při mrtvém přívodu tak nevzniká podtlak proti kamnům.
  - Vadný ventilátor dál dostává svůj povel. Porucha zmizí až po 30 s platných otáček.
  - Porucha obou ventilátorů: oba stojí a každých 15 min proběhne 2minutový zkušební běh na 30 %. Ventilátor, který se ozve, se uvolní.
- **Reference filtru:** krok se používá až po dokončení (10 min vzorků, příznak dokončení uložený ve flash). Učení přerušené restartem pokračuje.
  - Tlačítko **Filter recalibrate** naučí novou referenci bez vynulování stáří filtru. Okna 72 h a 720 h se počítají od kalibrace (`cfg[100-101]`).
  - Při přechodu na rozložení 2 (4. review) staré reference neměly příznak dokončení, proto se kalibrace automaticky spustí znovu. Stáří filtru zůstává.
  - Časovače poruch ventilátorů mají vlastní příznak běhu a přesný čas startu. Ověřeno modelem s 32bitovým přetečením. Text i alarm filtru berou odchylku jen se vzorkem z posledních 15 min.
- **Čidla NTC (2. review):**
  - odpor mimo 500 Ω–150 kΩ se nepublikuje (NAN), takže se nedostane do mediánu ani do řízení;
  - teploty se používají jen konečné, v rozsahu −40 až 70 °C a s posledním platným měřením do 2 min;
  - za TEMP1 je záloha z HA (`sensor.dum_prumerna_teplota_zigbee`, do 15 min).
- **Studený dům:** aktivní zastavení se při ztrátě čidla neruší. Uvolní ho až platné měření nad 7 °C.
- **Mráz v režimu Airflow** vždy zavře bypass, i v režimu Manual.
- **Ostatní:** „Filter replaced“ vynuluje i učení v paměti RAM (čítač výměn `cfg[82]`). Start po zapnutí se hlídá příznakem, ne přes `millis()`, takže přetečení po 49 dnech nevadí. Data z HA platí jen 15 min a alarm filtru potřebuje vzorek z poslední hodiny.
- **Vlhkost z HA** musí být čerstvá (do 30 min). Strop „suchý vzduch“ platí i nad volným chlazením. Volné chlazení běží i o dovolené.
- **Filtr:** bez použitelného vzorku 24 h hlásí „Cannot evaluate“, alarm počítá jen s čerstvým vyhodnocením.
- **Zabezpečení:** šifrované API, heslo OTA, heslo webového rozhraní, nové heslo záložního AP. Hodnoty jsou v `firmware/secrets.yaml` a ve verzi pro Builder.
- **„Bypass open“** v HA = **Bypass – relé sepnuté**: ukazuje relé, polohu klapky nikdo neměří.
- **Hardware rev D:** při resetu jsou GPIO13/14 plovoucí, tranzistor nevede a ventilátory na okamžik dostanou 100 %. Je potřeba pull-up na bázi.

**Oprava měření NTC (16. 10.):** TEMP1 ukazoval o ~4,6 °C víc. Plovoucí pin TX při měření TEMP1 vytahoval převodník CH340 a přes TEMP2 tekl proud do A0. Teď se neměřený pin drží na 0 V a oba odpory se dopočítají ze dvou měření. Po opravě: TEMP1 22,5 °C proti průměru Zigbee 21,9 °C, TEMP2 18,5 °C proti meteostanici 17,8 °C.

**Kamna** mají vlastní přívod vzduchu zvenku; kouř táhla jen při běžící digestoři. Ochrana proti mrazu je nastavená na Bypass, digestoř řeší režim Cooker hood. Chytrá zásuvka `switch.rekuperace_spinac` už se nevypíná (napájí i ESP).

### Co potřebuji vědět
- Máš v domě spotřebič s komínovým tahem (kotel, krb)?
- Jakou teplotu topíš v zimě? Komfortní mez pro bypass by byla o 3 °C výš.
- Můžeš na chvíli připojit starou desku a opsat Commissioning hodnoty?

---
Zdroje:
- [Sentinel Kinetic Installation & Commissioning (Vent-Axia, 2009)](http://www.i-acs.co.uk/store/documentation/datasheets/ventaxia/F&W_Instructions_439817_S.pdf)
- [Frost protection for MVHR (21 Degrees)](https://21degrees.com/guides/frost-protection-mvhr-heat-recovery-ventilation-systems)
- [Jak provozovat MVHR (Paul Heat Recovery)](https://www.paulheatrecovery.co.uk/information-on-domestic-ventilation-and-mvhr/how-to-operate-and-maintain-an-mvhr-system/)
- [Buildhub – Sentinel Kinetic diagnostic screens](https://forum.buildhub.org.uk/topic/14333-vent-axia-sentinel-kinetic-plus-b-diagnostic-screens)
