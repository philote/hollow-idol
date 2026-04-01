"""Main mold case generator.

Entry points:
    build_blank_mold(cfg, printer) -> dict
    build_model_mold(cfg, printer) -> dict  [not yet implemented]

The returned dict has keys:
    halves    – list of cq.Workplane, one per mold part (front → back)
    assembled – cq.Workplane of the full joined case (for preview)
    summary   – dict of human-readable metadata and any warnings
"""
from __future__ import annotations

import warnings as _warnings

import cadquery as cq

from hollow_idol.config import MoldConfig, PrinterConfig
from hollow_idol.natches import apply_natches

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_blank_mold(
    cfg: MoldConfig,
    printer: PrinterConfig,
) -> dict:
    """Generate a two-part blank mold case (no imported mesh).

    Each half is a thin-walled open tray.  The two halves are placed
    face-to-face along the Y-axis parting plane (Y=0).  Plaster is poured
    into the open face of each tray around the master form; once set the
    printed case is removed leaving a plaster mold half.

    Pipeline:
        1. Build base tray (floor at -Y, open at Y=0)
        2. Add exterior clamping clips
        3. Apply registration bumps to front half
        4. Mirror base tray to get back half (floor at +Y, open at Y=0)
        5. Apply registration divots to back half
        6. Assemble preview solid
        7. Validate against printer build volume

    Returns a dict with keys: halves, assembled, summary.
    """
    bw = cfg.blank_width
    bd = cfg.blank_depth
    bh = cfg.blank_height
    cw = cfg.case_wall

    half_depth = bd / 2.0

    # 1+2. Base tray with clips and orientation notch (no natches yet)
    base_tray = _build_tray_half(cfg)
    base_with_clips = _add_clips(base_tray, cfg)
    base_with_notch = _add_orientation_notch(base_with_clips, cfg)

    # Interior floor Y positions (design coords, before flat-lay rotation).
    # Front half: interior at -Y, floor face at -blank_depth/2.
    # Back half:  mirror of front → interior at +Y, floor face at +blank_depth/2.
    floor_y_front = -bd / 2.0
    floor_y_back  = +bd / 2.0

    # 3. Front half — convex key domes on interior floor, pointing +Y into cavity.
    front = apply_natches(base_with_notch, cfg, mode="bump", floor_y=floor_y_front)

    # 4. Back half — mirror base about XZ plane (negates Y).
    back_base = base_with_notch.mirror("XZ")

    # 5. Back half — concave key recesses cut into floor solid (+Y into material).
    #    Requires natch_radius ≤ case_wall/2 to avoid punching through the floor.
    back = apply_natches(back_base, cfg, mode="divot", floor_y=floor_y_back)

    halves = [front, back]

    # 6. Assembled preview
    assembled = front.union(back)

    # 7. Build volume warnings
    build_warnings: list[str] = []
    for i, half in enumerate(halves):
        label = f"half_{i}"
        build_warnings.extend(_check_build_volume(half, printer, label))

    if build_warnings:
        for w in build_warnings:
            _warnings.warn(w, stacklevel=2)

    outer_w = bw + 2.0 * cw
    outer_d = half_depth + cw
    outer_h = bh + 2.0 * cw

    summary = {
        "mode": "blank",
        "printer": printer.printer_name,
        "blank_dims_mm": (bw, bd, bh),
        "tray_outer_dims_mm": (outer_w, outer_d, outer_h),
        "case_wall_mm": cw,
        "split_axis": cfg.split_axis,
        "num_parts": len(halves),
        "shrink_factor": cfg.shrink_factor,
        "draft_angle_deg": cfg.draft_angle_deg,
        "natch_radius_mm": cfg.natch_radius,
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

def _build_tray_half(cfg: MoldConfig) -> cq.Workplane:
    """Build one open tray half with floor at -Y and open face at Y=0.

    Coordinate system:
        X — width  (interior spans ±blank_width/2)
        Y — depth  (floor outer face at -(blank_depth/2 + case_wall), open at Y=0)
        Z — height (interior spans ±blank_height/2)

    The inner void is a simple positioned box subtracted from the outer box,
    leaving case_wall thickness on the floor and all four side walls, with a
    fully open parting face at Y=0.
    """
    bw = cfg.blank_width
    bd_half = cfg.blank_depth / 2.0
    bh = cfg.blank_height
    cw = cfg.case_wall

    outer_w = bw + 2.0 * cw
    outer_d = bd_half + cw   # floor (cw thick) + interior depth (bd_half)
    outer_h = bh + 2.0 * cw

    # Outer box: centred so it spans Y ∈ [-(bd_half+cw), 0]
    cy_outer = -(bd_half + cw) / 2.0
    outer = (
        cq.Workplane("XY")
        .box(outer_w, outer_d, outer_h, centered=True)
        .translate((0.0, cy_outer, 0.0))
    )

    # Inner void: spans Y ∈ [-bd_half, +eps]
    # Removes the interior leaving case_wall on floor and side walls.
    # The +eps past Y=0 ensures the parting face is fully open.
    eps = 0.5
    inner_d = bd_half + eps
    cy_inner = (-bd_half + eps) / 2.0
    inner = (
        cq.Workplane("XY")
        .box(bw, inner_d, bh, centered=True)
        .translate((0.0, cy_inner, 0.0))
    )

    tray = outer.cut(inner)

    # Chamfer the 4 outer vertical edges (parallel to Y, at X×Z corners).
    # Select edges by length: vertical edges span the full outer depth (outer_d),
    # so we filter for edges parallel to Y (tangent direction ≈ Y-axis).
    if cfg.chamfer_size > 0:
        try:
            tray = (
                tray
                .edges("|Y")
                .chamfer(cfg.chamfer_size)
            )
        except Exception:
            # CadQuery chamfer can fail on complex topologies; skip gracefully.
            pass

    return tray


def _add_clips(tray: cq.Workplane, cfg: MoldConfig) -> cq.Workplane:
    """Add a symmetric pair of rectangular clamping clips to the ±X outer walls.

    Each clip is a tab that protrudes outward in X.  When both case halves are
    brought face-to-face the clips overlap and hold the assembly closed (or
    accept a rubber band / zip tie around them).

    Clips are centred at Z=0 and at Y mid-depth of the tray.
    """
    bw = cfg.blank_width
    bd_half = cfg.blank_depth / 2.0
    cw = cfg.case_wall

    clip_w = cfg.clip_width    # Y extent (along tray depth)
    clip_h = cfg.clip_height   # Z extent
    clip_d = cfg.clip_depth    # X protrusion beyond outer wall

    outer_w = bw + 2.0 * cw
    clip_centre_y = -(bd_half + cw) / 2.0   # Y mid-depth of tray

    for sign in (+1.0, -1.0):
        x_wall = sign * outer_w / 2.0
        x_centre = x_wall + sign * clip_d / 2.0

        clip = (
            cq.Workplane("XY")
            .box(clip_d, clip_w, clip_h, centered=True)
            .translate((x_centre, clip_centre_y, 0.0))
        )
        tray = tray.union(clip)

    return tray


def _add_orientation_notch(tray: cq.Workplane, cfg: MoldConfig) -> cq.Workplane:
    """Add a small asymmetric rectangular tab to the -Z exterior wall.

    The tab appears on the SAME side of both mold halves (both front and back),
    making the assembled case obviously asymmetric — you can tell by sight or
    touch that the halves can only go together one way.  It is NOT a male/female
    connection pair; it is purely an orientation cue.

    The tab protrudes outward in -Z from the bottom exterior wall, centred in X,
    at the Y mid-depth of the tray.
    """
    bw = cfg.blank_width
    bd_half = cfg.blank_depth / 2.0
    cw = cfg.case_wall
    ns = cfg.orientation_notch_size   # width and protrusion depth

    outer_h = cfg.blank_height + 2.0 * cw
    z_wall_outer = -(outer_h / 2.0)          # outer face of -Z wall
    z_notch_centre = z_wall_outer - ns / 2.0  # notch centred on that face
    y_mid = -(bd_half + cw) / 2.0             # Y mid-depth of tray

    notch = (
        cq.Workplane("XY")
        .box(ns, ns, ns, centered=True)
        .translate((0.0, y_mid, z_notch_centre))
    )
    return tray.union(notch)


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
    ow, od, oh = s["tray_outer_dims_mm"]
    print(
        f"\n=== hollow-idol mold summary ===\n"
        f"  Mode                : {s['mode']}\n"
        f"  Printer             : {s['printer']}\n"
        f"  Cavity (W×D×H)      : {bw:.0f} × {bd:.0f} × {bh:.0f} mm\n"
        f"  Tray outer (W×D×H)  : {ow:.0f} × {od:.0f} × {oh:.0f} mm\n"
        f"  Case wall thickness : {s['case_wall_mm']:.0f} mm\n"
        f"  Draft angle         : {s['draft_angle_deg']}°\n"
        f"  Shrink factor       : {s['shrink_factor']}\n"
        f"  Parts               : {s['num_parts']}\n"
    )
    if s["warnings"]:
        print("  Warnings:")
        for w in s["warnings"]:
            print(f"      {w}")
    else:
        print("  All halves fit within build volume.")
    print()
