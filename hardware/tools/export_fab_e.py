"""Rev E fabrication data for JLCPCB (mvhr_ctrl_jlcpcb.zip) and Gatema PCB (designer handbook 2026): ODB++ (preferred) + Gerber X2 + Excellon,
outline also as *-dim.ger (their recommended name), schematic PDF, BOM, 3D renders.
Hole sizes in the data are FINISHED sizes - say so in the order (Gatema p. 7)."""
import os
import shutil
import subprocess

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
PRJ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mvhr_ctrl"))
PCB = os.path.join(PRJ, "mvhr_ctrl.kicad_pcb")
SCH = os.path.join(PRJ, "mvhr_ctrl.kicad_sch")
FAB = os.path.join(PRJ, "fab")
GER = os.path.join(FAB, "gerber")


def cli(*a):
    subprocess.run([CLI, *a], check=True, capture_output=True)


shutil.rmtree(FAB, ignore_errors=True)
os.makedirs(GER, exist_ok=True)
cli("pcb", "export", "gerbers", "--layers", "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,Edge.Cuts", "--subtract-soldermask",
    "-o", GER + os.sep, PCB)
cli("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--excellon-units", "mm",
    "--generate-map", "--map-format", "pdf", "-o", GER + os.sep, PCB)
shutil.copy(os.path.join(GER, "mvhr_ctrl-Edge_Cuts.gm1"), os.path.join(GER, "mvhr_ctrl-dim.ger"))
cli("pcb", "export", "odb", "-o", os.path.join(FAB, "mvhr_ctrl_odb.zip"), PCB)
shutil.make_archive(os.path.join(FAB, "mvhr_ctrl_gerber"), "zip", GER)
# Gatema POOL servis layer names ("Kriteria dat pro POOL servis", 11/2025): *.top *.bot *.smt *.smb *.plt *.pth
# (plated, finished sizes) *.mill (non-plated holes) *.dim (outline)
POOL = os.path.join(FAB, "pool")
os.makedirs(POOL, exist_ok=True)
for src, ext in (("F_Cu.gtl", "top"), ("B_Cu.gbl", "bot"), ("F_Mask.gts", "smt"), ("B_Mask.gbs", "smb"),
                 ("F_Silkscreen.gto", "plt"), ("PTH.drl", "pth"), ("NPTH.drl", "mill"), ("Edge_Cuts.gm1", "dim")):
    shutil.copy(os.path.join(GER, "mvhr_ctrl-" + src), os.path.join(POOL, "mvhr_ctrl." + ext))
shutil.make_archive(os.path.join(FAB, "mvhr_ctrl_pool"), "zip", POOL)
# JLCPCB: the plain KiCad Gerber + Excellon set (their KiCad guide); order 1.6 mm, 1 oz, HASL lead-free
shutil.copy(os.path.join(FAB, "mvhr_ctrl_gerber.zip"), os.path.join(FAB, "mvhr_ctrl_jlcpcb.zip"))
cli("sch", "export", "pdf", "-o", os.path.join(PRJ, "mvhr_ctrl_schematic.pdf"), SCH)
# assembly drawing (review E-09): outline, silkscreen and the F.Fab layer with references AND values
cli("pcb", "export", "pdf", "--layers", "F.Fab,F.SilkS,Edge.Cuts", "--mode-single", "--include-border-title",
    "-o", os.path.join(PRJ, "mvhr_ctrl_assembly.pdf"), PCB)
cli("sch", "export", "bom", "--fields", "Reference,Value,Footprint,MPN,${QUANTITY}",
    "--labels", "Reference,Value,Footprint,MPN,Qty", "--group-by", "Value,Footprint", "--sort-field", "Reference",
    "--exclude-dnp", "-o", os.path.join(PRJ, "mvhr_ctrl_bom.csv"), SCH)
for side in ("top", "bottom"):
    cli("pcb", "render", "--side", side, "--width", "1600", "--height", "1100", "--quality", "high",
        "-o", os.path.join(PRJ, "render_%s.png" % side), PCB)
print("fab data in", FAB)
