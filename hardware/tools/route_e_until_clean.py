"""Rev E: build placement + Freerouting, repeated until the KiCad DRC reports 0 unconnected pads and 0 errors
(Freerouting is not deterministic; some runs leave a few nets open). Run with the system Python."""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KPY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
PRJ = os.path.normpath(os.path.join(HERE, "..", "mvhr_ctrl"))
env = dict(os.environ, VENTAXIA_PRJ="mvhr_ctrl", VENTAXIA_BUILD="build_pcb_e", VENTAXIA_FR_PASSES="60")

for attempt in range(1, int(sys.argv[1]) + 1 if len(sys.argv) > 1 else 9):
    subprocess.run([KPY, os.path.join(HERE, "build_pcb_e.py")], check=True, env=env, capture_output=True)
    subprocess.run([KPY, os.path.join(HERE, "route.py")], check=True, env=env, capture_output=True)
    rpt = os.path.join(PRJ, "drc.rpt")
    subprocess.run([CLI, "pcb", "drc", "--schematic-parity", "--refill-zones", "-o", rpt,
                    os.path.join(PRJ, "mvhr_ctrl.kicad_pcb")], capture_output=True)
    t = open(rpt, encoding="utf-8").read()
    unconnected = int(re.search(r"Found (\d+) unconnected", t).group(1))
    errors = len([m for m in re.findall(r"^\[(\w+)\]", t, re.M) if m != "lib_footprint_mismatch"])
    print("attempt %d: unconnected %d, other DRC items %d" % (attempt, unconnected, errors), flush=True)
    if unconnected == 0 and errors == 0:
        break
else:
    sys.exit("no clean routing")
