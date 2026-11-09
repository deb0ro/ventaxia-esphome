# Generates hw/firmware/ventaxia_alpha.yaml (+ _builder copy with the secrets inlined, for the ESPHome Builder)
# from fw_template.yaml and one settings table. Run: python hw/firmware/gen/gen_fw.py
# To add a setting: give it a free cfg index (102-127) in NUMS/SWS/DTS, put it in SINCE with LAYOUT + 1 and raise
# LAYOUT. Existing indices must never move. cfg[83] = layout of the stored record; at boot every setting with a
# newer 'since' gets its default, so an added setting never starts at 0 and nothing else is reset.
LAYOUT = 3
import os
SC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(SC)          # hw/firmware

# key, cfg index, HA name (unchanged = same entity_id), min, max, step, unit, default, encoding, extra
NUMS = [
    ('low_sup', 4, 'Low supply %', 0, 100, 1, '%', 35, 'u8', ''),
    ('low_ext', 5, 'Low extract %', 0, 100, 1, '%', 40, 'u8', ''),
    ('norm_sup', 6, 'Normal supply %', 0, 100, 1, '%', 50, 'u8', ''),
    ('norm_ext', 7, 'Normal extract %', 0, 100, 1, '%', 55, 'u8', ''),
    ('boost_sup', 8, 'Boost supply %', 0, 100, 1, '%', 75, 'u8', ''),
    ('boost_ext', 9, 'Boost extract %', 0, 100, 1, '%', 80, 'u8', ''),
    ('night_sup', 10, 'Night supply %', 0, 100, 1, '%', 40, 'u8', ''),
    ('night_ext', 11, 'Night extract %', 0, 100, 1, '%', 40, 'u8', ''),
    ('hol_sup', 12, 'Holiday supply %', 0, 100, 1, '%', 25, 'u8', ''),
    ('hol_ext', 13, 'Holiday extract %', 0, 100, 1, '%', 30, 'u8', ''),
    ('cool_sup', 14, 'Free cooling supply %', 0, 100, 1, '%', 60, 'u8', ''),
    ('cool_ext', 15, 'Free cooling extract %', 0, 100, 1, '%', 60, 'u8', ''),
    ('fire_sup', 16, 'Fireplace supply %', 0, 100, 1, '%', 60, 'u8', ''),
    ('fire_ext', 17, 'Fireplace extract %', 0, 100, 1, '%', 30, 'u8', ''),
    ('hood_sup', 18, 'Cooker hood supply %', 0, 100, 1, '%', 60, 'u8', ''),
    ('hood_ext', 19, 'Cooker hood extract %', 0, 100, 1, '%', 0, 'u8', ''),
    ('man_sup', 20, 'Manual supply %', 0, 100, 1, '%', 50, 'u8', 'slider'),
    ('man_ext', 21, 'Manual extract %', 0, 100, 1, '%', 55, 'u8', 'slider'),
    ('rh_min', 22, 'Humidity minimum', 20, 50, 1, '%', 35, 'u8', ''),
    ('fire_minutes', 23, 'Fireplace duration', 5, 60, 5, 'min', 15, 'u8', 'noctl'),
    ('boost_minutes', 24, 'Boost duration', 5, 120, 5, 'min', 30, 'u8', 'noctl'),
    ('ramp_rate', 25, 'Fan ramp rate', 0.5, 20, 0.5, '%/s', 2, 'x2', 'noctl'),
    ('comfort_temp', 26, 'Bypass comfort temperature', 16, 30, 0.5, '°C', 24, 'x2', ''),
    ('outdoor_min', 27, 'Bypass outdoor minimum', 5, 20, 0.5, '°C', 14, 'x2', ''),
    ('frost_start', 28, 'Frost protection start', -10, 5, 0.5, '°C', 0, 'x2o20', ''),
    ('filter_days', 29, 'Filter change interval', 30, 730, 10, 'd', 180, 'd10', 'noctl'),
    ('filter_alarm', 30, 'Filter clog alarm', 3, 50, 1, '%', 15, 'u8', 'noctl'),
    # layout 1 (17.10.2026): scheduled airing
    ('purge_minutes', 91, 'Airing duration', 5, 120, 5, 'min', 30, 'u8', ''),
    ('purge_sup', 92, 'Airing supply %', 0, 100, 1, '%', 100, 'u8', ''),
    ('purge_ext', 93, 'Airing extract %', 0, 100, 1, '%', 100, 'u8', ''),
    # layout 3 (18.10.2026): airing times on Sat / Sun move by this many hours (with "Weekend night times")
    ('purge_we_h', 102, 'Weekend airing offset', 0, 4, 1, 'h', 1, 'u8', ''),
]
# extra C++ run once when a stored record is upgraded to that layout (after the defaults of that layout)
UPGRADE_CODE = {
    2: [
        '// layout 2 (review 4): references from layout 1 have no completion bit. They cannot be trusted as',
        '// complete, so the calibration restarts NOW (base = current run hours) - old values are only the start',
        '// of the new average; the filter age (cfg[40-43]) is kept.',
        'for (int i = 94; i < 100; i++) c[i] = 0;',
        'c[100] = c[44]; c[101] = c[45];',
    ],
}
SINCE = {'purge_minutes': 1, 'purge_sup': 1, 'purge_ext': 1, 'purge_on_1': 1, 'purge_on_2': 1, 'purge_on_3': 1,
         'purge_1': 1, 'purge_2': 1, 'purge_3': 1,
         'purge_we_h': 3}
ENC = {'u8': 'lroundf(x)', 'x2': 'lroundf(x * 2.0f)', 'x2o20': 'lroundf((x + 20.0f) * 2.0f)', 'd10': 'lroundf(x / 10.0f)'}
DEC = {'u8': 'c[{i}]', 'x2': 'c[{i}] / 2.0f', 'x2o20': 'c[{i}] / 2.0f - 20.0f', 'd10': 'c[{i}] * 10.0f'}
def enc_const(e, v):
    return {'u8': v, 'x2': v * 2, 'x2o20': (v + 20) * 2, 'd10': v / 10}[e]

# switch id, (cfg byte, bit), HA name, default, icon, config category  (cfg[3] bit0 = frost Bypass mode)
SWS = [
    ('summer_mode', (3, 1), 'Summer bypass', 1, 'mdi:weather-sunny', False),
    ('night_mode', (3, 2), 'Night mode', 1, 'mdi:weather-night', False),
    ('holiday_mode', (3, 3), 'Holiday', 0, 'mdi:bag-suitcase', False),
    ('dry_protect', (3, 4), 'Dry air protection', 1, 'mdi:water-percent-alert', True),
    ('free_cooling', (3, 5), 'Free cooling', 1, 'mdi:snowflake-thermometer', True),
    ('weekend_night', (3, 6), 'Weekend night times', 1, 'mdi:calendar-weekend', True),
    ('man_bypass', (3, 7), 'Manual bypass', 0, 'mdi:valve', False),
    ('purge_on_1', (84, 0), 'Airing 1 enabled', 1, 'mdi:weather-windy', True),
    ('purge_on_2', (84, 1), 'Airing 2 enabled', 1, 'mdi:weather-windy', True),
    ('purge_on_3', (84, 2), 'Airing 3 enabled', 1, 'mdi:weather-windy', True),
]
# datetime id, cfg index (hour, minute+1), HA name, default h, m
DTS = [
    ('night_start', 31, 'Night start', 22, 0),
    ('night_end', 33, 'Night end', 8, 0),
    # cfg[35-38] (former 'Night start/end weekend') are free since 18.10.2026: on the weekend both night times
    # are the weekday ones + 'Weekend airing offset'
    ('purge_1', 85, 'Airing 1 time', 8, 0),
    ('purge_2', 87, 'Airing 2 time', 12, 0),
    ('purge_3', 89, 'Airing 3 time', 19, 0),
]

def fmt(v):
    return ('%g' % v)


def render(tpl, SWS):
    numbers = []
    for k, i, name, mn, mx, st, unit, d, e, ex in NUMS:
        mode = 'slider' if ex == 'slider' else 'box'
        cat = '' if ex == 'slider' else ', entity_category: config'
        ctl = '' if ex == 'noctl' else ', script.execute: control'
        numbers.append(
            f'  - {{ platform: template, id: {k}, name: "{name}", min_value: {fmt(mn)}, max_value: {fmt(mx)}, step: {fmt(st)}, '
            f'unit_of_measurement: "{unit}", optimistic: true, initial_value: {fmt(d)}{cat}, mode: {mode}, '
            f'on_value: [lambda: "if (id(cfg_ready)) id(cfg)[{i}] = (uint8_t) {ENC[e]};"{ctl}] }}')
    NUMBERS = '\n'.join(numbers)

    switches = []
    for k, (byte, b), name, d, icon, cfgc in SWS:
        cat = '\n    entity_category: config' if cfgc else ''
        switches.append(f'''  - platform: template
    id: {k}
    name: "{name}"
    icon: {icon}
    optimistic: true
    restore_mode: ALWAYS_OFF      # real state comes from the settings record (cfg) at boot{cat}
    on_turn_on: [lambda: "if (id(cfg_ready)) id(cfg)[{byte}] |= (1 << {b});", script.execute: control]
    on_turn_off: [lambda: "if (id(cfg_ready)) id(cfg)[{byte}] &= ~(1 << {b});", script.execute: control]''')
    SWITCHES = '\n'.join(switches)

    dts = []
    for k, i, name, h, m in DTS:
        dts.append(f'''  - platform: template
    id: {k}
    name: "{name}"
    type: time
    optimistic: true
    initial_value: "{h:02d}:{m:02d}:00"
    entity_category: config
    on_value:
      - lambda: "if (id(cfg_ready)) {{ id(cfg)[{i}] = id({k}).hour; id(cfg)[{i + 1}] = id({k}).minute; }}"
      - script.execute: control''')
    DATETIMES = '\n'.join(dts)

    def default_lines(layout):
        out = []
        for k, i, name, mn, mx, st, unit, d, e, ex in NUMS:
            if SINCE.get(k, 0) == layout:
                out.append(f'c[{i}] = {int(round(enc_const(e, d)))};'.ljust(33) + f'// {name} = {fmt(d)}')
        for k, (byte, b), name, d, icon, cfgc in SWS:
            if SINCE.get(k, 0) == layout:
                op = f'c[{byte}] |= (1 << {b});' if d else f'c[{byte}] &= ~(1 << {b});'
                out.append(op.ljust(33) + f'// {name} = ' + ('on' if d else 'off'))
        for k, i, name, h, m in DTS:
            if SINCE.get(k, 0) == layout:
                out.append(f'c[{i}] = {h}; c[{i + 1}] = {m};'.ljust(33) + f'// {name}')
        return out

    defaults = ['c.fill(0);', 'c[0] = ${cfg_magic};', 'c[1] = ${cfg_version};', 'c[2] = 0;                        // mode Auto',
                'c[3] = 0x01;                     // bit0 frost Bypass mode (stove in the house, our choice 16.10.2026)']
    defaults += default_lines(0)
    upgrades = []
    for lay in range(1, LAYOUT + 1):
        upgrades.append(f'if (c[83] < {lay}) {{                  // settings added in layout {lay}')
        upgrades += ['  ' + l for l in default_lines(lay)]
        upgrades += ['  ' + l for l in UPGRADE_CODE.get(lay, [])]
        upgrades.append('}')
    upgrades.append(f'c[83] = {LAYOUT};')
    DEFAULTS = '\n'.join('              ' + l for l in defaults)
    UPGRADES = '\n'.join('            ' + l for l in upgrades)

    sync = []
    for k, i, name, mn, mx, st, unit, d, e, ex in NUMS:
        dec = DEC[e].format(i=i)
        sync.append(f'num(id({k}), {dec}, {float(mn)!r}f, {float(mx)!r}f, {float(d)!r}f);')
    for k, (byte, b), name, d, icon, cfgc in SWS:
        sync.append(f'id({k}).publish_state((c[{byte}] >> {b}) & 1);')
    for k, i, name, h, m in DTS:
        sync.append(f'id({k}).make_call().set_time(c[{i}] % 24, c[{i + 1}] % 60, 0).perform();')
    SYNC = '\n'.join('            ' + l for l in sync)

    s = tpl.replace('@@NUMBERS@@', NUMBERS).replace('@@SWITCHES@@', SWITCHES).replace('@@DATETIMES@@', DATETIMES)
    s = s.replace('@@DEFAULTS@@', DEFAULTS).replace('@@UPGRADES@@', UPGRADES).replace('@@SYNC@@', SYNC)
    assert '@@' not in s
    return s


import re
_sp = os.path.join(OUT, 'secrets.yaml')     # optional: without it no _builder copies are written
_sec = dict(re.findall(r'^(\w+):\s*"([^"]*)"', open(_sp, encoding='utf-8').read(), re.M)) if os.path.exists(_sp) else {}
sec = [_sec['api_encryption_key'], _sec['ota_password'], _sec['web_password'], _sec['ap_password']] if _sec else None


NL = chr(10)


def write(name, s):
    open(os.path.join(OUT, name + '.yaml'), 'w', encoding='utf-8', newline=NL).write(s)
    if sec is None:
        print('ok', name, len(s), '(no secrets.yaml, no _builder copy)')
        return
    b = (s.replace('!secret api_encryption_key', '"%s"' % sec[0])
          .replace('!secret ota_password', '"%s"' % sec[1])
          .replace('!secret web_password', '"%s"' % sec[2])
          .replace('!secret ap_password', '"%s"' % sec[3]))
    assert '!secret api_' not in b and '!secret ota' not in b and '!secret web' not in b and '!secret ap_' not in b
    open(os.path.join(OUT, name + '_builder.yaml'), 'w', encoding='utf-8', newline=NL).write(b)
    print('ok', name, len(s), len(b))


tpl = open(os.path.join(SC, 'fw_template.yaml'), encoding='utf-8').read()
write('ventaxia_alpha', render(tpl, SWS))                        # NodeMCU alpha (in the unit now)
import sys
sys.path.insert(0, SC)
import reve
write('ventaxia_reve', reve.transform(render(tpl, SWS + reve.SWS_EXTRA)))   # rev E board (hw/mvhr_ctrl)
