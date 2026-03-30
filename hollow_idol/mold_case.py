"""Main mold case generator.

Entry points:
    build_blank_mold(cfg, printer) -> dict
    build_model_mold(cfg, printer) -> dict  [not yet implemented]

The returned dict has keys:
    halves    – list of cq.Workplane, one per mold part (bottom → top)
    assembled – cq.Workplane of the full joined block (for preview)
    summary   – dict of human-readable metadata and any warnings
"""
from __future__ import annotations

import math
import warnings as _warnings

import cadquery as cq

from hollow_idol.config import MoldConfig, PrinterConfig
from hollow_idol.natches import apply_natches
from hollow_idol.slip_well import add_slip_well
from hollow_idol.split import split_mold

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_blank_mold(
    cfg: MoldConfig,
    printer: PrinterConfig,
) -> dict:
    """Generate a two-part blank mold (no imported mesh).

    Pipeline:
        1. Outer shell box
        2. Lofted inner cavity with draft angles
        3. Hollow the shell
        4. Flange around parting edge
        5. Split into halves
        6. Add natches (bumps on bottom, divots on top)
        7. Add slip well to top half
        8. Validate against printer build volume

    Returns a dict with keys: halves, assembled, summary.
    """
    bw = cfg.blank_width
    bd = cfg.blank_depth
    bh = cfg.blank_height
    wt = cfg.wall_thickness

    outer_w = bw + 2.0 * wt
    outer_d = bd + 2.0 * wt
    outer_h = bh + 2.0 * wt

    # 1. Outer shell
    outer = cq.Workplane("XY").box(outer_w, outer_d, outer_h, centered=True)

    # 2. Inner cavity — lofted to apply draft angles
    inner_void = _lofted_cavity(cfg)

    # 3. Hollow: subtract cavity from shell
    mold_block = outer.cut(inner_void)

    # 4. Flange ring at parting plane
    flange = _make_flange(outer_w, outer_d, cfg.flange_width, cfg.flange_thickness)
    assembled = mold_block.union(flange)

    # 5. Split
    halves = split_mold(assembled, cfg)
    if len(halves) != cfg.num_parts:
        _warnings.warn(
            f"Expected {cfg.num_parts} halves but produced {len(halves)}.",
            stacklevel=2,
        )

    # halves[0] = bottom (Z ≤ 0), halves[-1] = top (Z ≥ 0)
    bot_half = halves[0]
    top_half = halves[-1]

    # 6. Natches
    bot_half = apply_natches(bot_half, cfg, mode="bump")
    top_half = apply_natches(top_half, cfg, mode="divot")

    # 7. Slip well in top half
    top_z = outer_h / 2.0
    top_half = add_slip_well(top_half, cfg, top_z=top_z)

    halves = [bot_half] + halves[1:-1] + [top_half]

    # 8. Build volume warnings
    build_warnings: list[str] = []
    for i, half in enumerate(halves):
        label = f"half_{i}"
        build_warnings.extend(_check_build_volume(half, printer, label))

    if build_warnings:
        for w in build_warnings:
            _warnings.warn(w, stacklevel=2)

    summary = {
        "mode": "blank",
        "printer": printer.printer_name,
        "blank_dims_mm": (bw, bd, bh),
        "outer_dims_mm": (outer_w, outer_d, outer_h),
        "num_parts": len(halves),
        "shrink_factor": cfg.shrink_factor,
        "draft_angle_deg": cfg.draft_angle_deg,
        "wall_thickness_mm": wt,
        "flange_width_mm": cfg.flange_width,
        "natch_radius_mm": cfg.natch_radius,
        "slip_well_diameter_mm": cfg.slip_well_diameter,
        "warnings": build_warnings,
    }

    _print_summary(summary)

    return {
        "halves": halves,
        "assembled": assembled,
        "summary": summary,
    }


def build_model_mold(
    cfg: MoldConfig,
    printer: PrinterConfig,
) -> dict:
    """Generate a mold from an imported watertight STL.

    Not yet implemented.  Provide a model_file path in MoldConfig when ready.
    """
    raise NotImplementedError(
        "Model mode is not yet implemented.  "
        "Set cfg.model_file=None and use build_blank_mold() for blank mode."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _lofted_cavity(cfg: MoldConfig) -> cq.Workplane:
    """Lofted inner void with draft angle taper.

    The cavity is widest at the parting plane (Z=0) and narrows toward the
    closed ends, giving the required draft for easy demolding.

    Returns a single solid spanning Z ∈ [-blank_height/2, +blank_height/2].
    """
    w0 = cfg.blank_width
    d0 = cfg.blank_depth
    half_h = cfg.blank_height / 2.0

    taper = half_h * math.tan(math.radians(cfg.draft_angle_deg))
    w1 = max(w0 - 2.0 * taper, 1.0)
    d1 = max(d0 - 2.0 * taper, 1.0)

    # Small overlap past Z=0 so the two lofts union cleanly without gap
    eps = 0.01

    inner_bottom = (
        cq.Workplane("XY")          # Z = 0
        .rect(w0, d0)
        .workplane(offset=-(half_h + eps))
        .rect(w1, d1)
        .loft()
    )
    inner_top = (
        cq.Workplane("XY")          # Z = 0
        .rect(w0, d0)
        .workplane(offset=(half_h + eps))
        .rect(w1, d1)
        .loft()
    )

    return inner_bottom.union(inner_top)


def _make_flange(
    outer_w: float,
    outer_d: float,
    flange_width: float,
    flange_thickness: float,
) -> cq.Workplane:
    """Rectangular ring flange centred at Z=0.

    The flange extends outward from the mold body walls by flange_width,
    and spans Z ∈ [-flange_thickness/2, +flange_thickness/2].
    """
    fo_w = outer_w + 2.0 * flange_width
    fo_d = outer_d + 2.0 * flange_width

    flange_box = cq.Workplane("XY").box(fo_w, fo_d, flange_thickness, centered=True)
    # Punch out the mold body footprint (with a tiny clearance to avoid coincident faces)
    punch = cq.Workplane("XY").box(
        outer_w - 0.01, outer_d - 0.01, flange_thickness + 1.0, centered=True
    )
    return flange_box.cut(punch)


def _check_build_volume(
    half: cq.Workplane,
    printer: PrinterConfig,
    label: str,
) -> list[str]:
    """Return warning strings if any dimension of half exceeds the printer bed."""
    bb = half.val().BoundingBox()
    dx = bb.xmax - bb.xmin
    dy = bb.ymax - bb.ymin
    dz = bb.zmax - bb.zmin

    warnings: list[str] = []
    if dx > printer.bed_x:
        warnings.append(
            f"[{label}] X={dx:.1f}mm exceeds printer bed_x={printer.bed_x:.1f}mm"
        )
    if dy > printer.bed_y:
        warnings.append(
            f"[{label}] Y={dy:.1f}mm exceeds printer bed_y={printer.bed_y:.1f}mm"
        )
    if dz > printer.bed_z:
        warnings.append(
            f"[{label}] Z={dz:.1f}mm exceeds printer bed_z={printer.bed_z:.1f}mm"
        )
    return warnings


def _print_summary(s: dict) -> None:
    bw, bd, bh = s["blank_dims_mm"]
    ow, od, oh = s["outer_dims_mm"]
    print(
        f"\n=== hollow-idol mold summary ===\n"
        f"  Mode           : {s['mode']}\n"
        f"  Printer        : {s['printer']}\n"
        f"  Cavity (W×D×H) : {bw:.0f} × {bd:.0f} × {bh:.0f} mm\n"
        f"  Outer  (W×D×H) : {ow:.0f} × {od:.0f} × {oh:.0f} mm\n"
        f"  Wall thickness : {s['wall_thickness_mm']:.0f} mm\n"
        f"  Draft angle    : {s['draft_angle_deg']}°\n"
        f"  Shrink factor  : {s['shrink_factor']}\n"
        f"  Parts          : {s['num_parts']}\n"
    )
    if s["warnings"]:
        print("  ⚠ Warnings:")
        for w in s["warnings"]:
            print(f"      {w}")
    else:
        print("  ✓ All halves fit within build volume.")
    print()
