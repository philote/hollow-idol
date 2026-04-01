"""
Core mold-half geometry, parameterised via MoldConfig.

Public API:
    build_half_a(cfg) -> Part   convex keys + ID notch
    build_half_b(cfg) -> Part   concave keys, no notch
    generate(cfg, printer)      build both halves, warn on bed overrun, return (part_a, part_b)
"""

import warnings
from build123d import *

from hollow_idol.config import MoldConfig, PrinterConfig


# ── Internal builder ───────────────────────────────────────────────────────────

def _build_tray(cfg: MoldConfig, *, convex_keys: bool, has_notch: bool) -> Part:
    """
    Builds one mold-half tray.

    convex_keys=True  → hemisphere bumps ADD to interior floor (Half A)
    convex_keys=False → hemisphere divots SUBTRACT from interior floor (Half B)
    has_notch=True    → rectangular ID notch on −Y interior wall (Half A only)
    """
    c = cfg  # short alias

    # Derived
    inner_x      = c.outer_x - 2 * c.wall
    inner_y      = c.outer_y - 2 * c.wall
    inner_z      = c.outer_z - c.wall      # open top — no ceiling
    inner_cx     = inner_x / 2
    inner_cy     = inner_y / 2
    inner_floor_z = c.wall
    mid_z        = inner_floor_z + inner_z / 2

    with BuildPart() as mold:

        # 1. Outer box (sits on XY plane)
        Box(c.outer_x, c.outer_y, c.outer_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 2. Hollow interior — WALL-thick floor + walls, open top
        with Locations((0, 0, inner_floor_z)):
            Box(inner_x, inner_y, inner_z,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT)

        # 3. Chamfer interior edges
        #    - 4 vertical corner edges of the cavity
        #    - 4 floor-wall edges at z=inner_floor_z
        vert_interior = [
            e for e in mold.edges()
            if (abs(abs(e.center().X) - inner_cx) < 0.5 and
                abs(abs(e.center().Y) - inner_cy) < 0.5 and
                abs(e.center().Z - mid_z) < 0.5)
        ]
        floor_wall = [
            e for e in mold.edges()
            if (abs(e.center().Z - inner_floor_z) < 0.5 and
                (abs(abs(e.center().X) - inner_cx) < 0.5 or
                 abs(abs(e.center().Y) - inner_cy) < 0.5))
        ]
        interior_edges = vert_interior + floor_wall
        assert len(interior_edges) == 8, (
            f"Expected 8 interior edges for chamfer, got {len(interior_edges)}."
        )
        chamfer(interior_edges, length=c.chamfer)

        # 4. Registration keys
        hemi_x = inner_cx - c.hemi_offset
        hemi_y = inner_cy - c.hemi_offset

        if convex_keys:
            # Sphere centre sunk below floor; dome of hemi_height protrudes up
            hemi_cz = inner_floor_z - (c.hemi_r - c.hemi_height)
            with Locations(
                ( hemi_x,  hemi_y, hemi_cz),
                ( hemi_x, -hemi_y, hemi_cz),
                (-hemi_x,  hemi_y, hemi_cz),
                (-hemi_x, -hemi_y, hemi_cz),
            ):
                Sphere(c.hemi_r)

            # Clip any sphere material that pokes below z=0
            clip = c.hemi_r
            with Locations((0, 0, -clip / 2)):
                Box(c.outer_x + 2, c.outer_y + 2, clip, mode=Mode.SUBTRACT)

        else:
            # Sphere centre raised above floor; cuts a pocket of hemi_height deep
            hemi_cz = inner_floor_z + (c.hemi_r - c.hemi_height)
            with Locations(
                ( hemi_x,  hemi_y, hemi_cz),
                ( hemi_x, -hemi_y, hemi_cz),
                (-hemi_x,  hemi_y, hemi_cz),
                (-hemi_x, -hemi_y, hemi_cz),
            ):
                Sphere(c.hemi_r, mode=Mode.SUBTRACT)

        # 5. ID notch on −Y interior wall (Half A only)
        if has_notch:
            notch_cy = -(inner_cy - c.notch_w / 2)
            notch_cz = inner_floor_z + c.notch_h / 2
            with Locations((0, notch_cy, notch_cz)):
                Box(c.notch_l, c.notch_w, c.notch_h, mode=Mode.SUBTRACT)

    return mold.part


# ── Public builders ────────────────────────────────────────────────────────────

def build_half_a(cfg: MoldConfig) -> Part:
    """Convex registration keys + identification notch."""
    return _build_tray(cfg, convex_keys=True, has_notch=True)


def build_half_b(cfg: MoldConfig) -> Part:
    """Concave registration keys, no notch."""
    return _build_tray(cfg, convex_keys=False, has_notch=False)


# ── Top-level generate ─────────────────────────────────────────────────────────

def generate(cfg: MoldConfig, printer: PrinterConfig) -> tuple[Part, Part]:
    """
    Build both mold halves and warn if either exceeds the printer bed.
    Returns (half_a, half_b).
    """
    half_a = build_half_a(cfg)
    half_b = build_half_b(cfg)

    for label, part in [("Half A", half_a), ("Half B", half_b)]:
        bb = part.bounding_box()
        sx = bb.max.X - bb.min.X
        sy = bb.max.Y - bb.min.Y
        sz = bb.max.Z - bb.min.Z
        overruns = []
        if sx > printer.bed_x:
            overruns.append(f"X {sx:.1f} > bed {printer.bed_x}")
        if sy > printer.bed_y:
            overruns.append(f"Y {sy:.1f} > bed {printer.bed_y}")
        if sz > printer.bed_z:
            overruns.append(f"Z {sz:.1f} > bed {printer.bed_z}")
        if overruns:
            warnings.warn(
                f"{label} exceeds {printer.printer_name} build volume: {', '.join(overruns)}",
                stacklevel=2,
            )

    return half_a, half_b
