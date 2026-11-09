"""Load symbols from KiCad's stock libraries, flattening `extends`."""
import copy
import os

from sexp import Sym, find, find_all, parse

KICAD_SHARE = r"C:\Program Files\KiCad\10.0\share\kicad"
SYM_DIR = os.path.join(KICAD_SHARE, "symbols")

_lib_cache = {}


def _load_lib(lib):
    if lib not in _lib_cache:
        with open(os.path.join(SYM_DIR, lib + ".kicad_sym"), encoding="utf-8") as f:
            tree = parse(f.read())
        _lib_cache[lib] = {s[1]: s for s in find_all(tree, "symbol")}
    return _lib_cache[lib]


def get_symbol(lib_id):
    """Return a flattened symbol definition named `lib_id` (e.g. 'Device:R')."""
    lib, name = lib_id.split(":", 1)
    syms = _load_lib(lib)
    sym = copy.deepcopy(syms[name])
    ext = find(sym, "extends")
    if ext:
        parent = get_symbol(lib + ":" + ext[1])
        parent_name = parent[1].split(":", 1)[1]
        flat = [Sym("symbol"), lib_id]
        child_props = {p[1]: p for p in find_all(sym, "property")}
        for item in parent[2:]:
            if isinstance(item, list) and item[0] == "property" and item[1] in child_props:
                flat.append(child_props.pop(item[1]))
            elif isinstance(item, list) and item[0] == "symbol":
                sub = copy.deepcopy(item)
                sub[1] = sub[1].replace(parent_name, name, 1)
                flat.append(sub)
            else:
                flat.append(item)
        # child-only properties go before the unit sub-symbols
        idx = next(i for i, x in enumerate(flat) if isinstance(x, list) and x[0] == "symbol")
        for p in child_props.values():
            flat.insert(idx, p)
            idx += 1
        return flat
    sym[1] = lib_id
    return sym


def pins(sym, unit=1):
    """List of dicts: number, name, x, y, angle, type for the given unit (plus common unit 0)."""
    out = []
    for sub in find_all(sym, "symbol"):
        parts = sub[1].rsplit("_", 2)
        u = int(parts[-2])
        if u not in (0, unit):
            continue
        for p in find_all(sub, "pin"):
            at = find(p, "at")
            out.append({
                "type": str(p[1]),
                "x": float(at[1]),
                "y": float(at[2]),
                "angle": float(at[3]) if len(at) > 3 else 0.0,
                "name": find(p, "name")[1],
                "number": find(p, "number")[1],
                "hidden": any(x == "hide" or (isinstance(x, list) and x[0] == "hide" and x[1] == "yes") for x in p),
            })
    return out


if __name__ == "__main__":
    import sys
    for lid in sys.argv[1:]:
        s = get_symbol(lid)
        print("==", lid)
        for p in sorted(pins(s), key=lambda p: (p["number"].zfill(3))):
            print("  %-4s %-14s %-12s (%g,%g) a%g" % (p["number"], p["name"], p["type"], p["x"], p["y"], p["angle"]))
