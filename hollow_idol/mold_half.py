"""Half A — convex keys + ID notch. Run directly to regenerate output/mold_half_a.stl."""
import os
from build123d import export_stl
from hollow_idol.config import MoldConfig
from hollow_idol.mold_case import build_half_a
from hollow_idol import printers

cfg     = MoldConfig()
printer = printers.DEFAULT

part = build_half_a(cfg)

bb = part.bounding_box()
sx, sy, sz = bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z
for dim, size, bed in [("X", sx, printer.bed_x), ("Y", sy, printer.bed_y), ("Z", sz, printer.bed_z)]:
    if size > bed:
        print(f"WARNING: Half A {dim} {size:.1f} mm exceeds {printer.printer_name} bed ({bed} mm)")

os.makedirs("output", exist_ok=True)
export_stl(part, "output/mold_half_a.stl")
print("Exported: output/mold_half_a.stl")
