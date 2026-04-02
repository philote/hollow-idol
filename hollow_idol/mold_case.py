"""
3-piece mold case geometry, parameterised via MoldConfig.

Each mold half is made of three parts:
  - wall_left  / wall_right : C-shaped `[` and `]` wall frames
  - bottom                  : sliding floor panel with registration keys

Public API:
    build_wall_piece(cfg) -> Part   C-frame (mirror in X for the other side)
    build_bottom(cfg, *, convex_keys, has_notch) -> Part
    generate(cfg, printer) -> (wall_left_a, wall_right_a, bottom_a,
                                wall_left_b, wall_right_b, bottom_b)
"""

import warnings
from build123d import *

from hollow_idol.config import MoldConfig, PrinterConfig


# ── Wall piece ─────────────────────────────────────────────────────────────────

def build_wall_piece(cfg: MoldConfig) -> Part:
    """
    C-shaped `[` wall frame (one of two per mold half).

    Geometry (top view):
      ┌──────────────────────┐  ← long outer wall  (full outer_x wide)
      │    (interior)        │
      │                      │  ← two arms, each outer_y/2 deep
      └──────────────────────┘

    The groove is formed by additive top rails on the inner face of all three
    walls (U-path). The C-piece floor is the bottom surface; each rail
    overhangs the panel edge to retain it. Panel slides along the floor.
    Flanges project outward from the open arm-tip faces.

    Mirror in X to get the `]` piece.
    """
    c = cfg

    arm_y = c.outer_y / 2
    inner_x = c.outer_x - 2 * c.wall

    with BuildPart() as wp:

        # ── 1. Three wall slabs ────────────────────────────────────────────
        # Back wall — full X width, wall thick, full Z
        with Locations((0, -(c.outer_y / 2 - c.wall / 2), c.outer_z / 2)):
            Box(c.outer_x, c.wall, c.outer_z)

        # Left arm (−X end)
        with Locations((-(c.outer_x / 2 - c.wall / 2), -arm_y / 2, c.outer_z / 2)):
            Box(c.wall, arm_y, c.outer_z)

        # Right arm (+X end)
        with Locations(((c.outer_x / 2 - c.wall / 2), -arm_y / 2, c.outer_z / 2)):
            Box(c.wall, arm_y, c.outer_z)

        # ── 2. Back wall top rail (additive) ──────────────────────────────
        # Protrudes groove_depth in +Y from back wall inner face.
        # Bottom face of rail at Z = groove_width; panel slides under it.
        back_inner_y = -(c.outer_y / 2 - c.wall)
        rail_cz = c.groove_width + c.groove_depth / 2
        with Locations((0, back_inner_y + c.groove_depth / 2, rail_cz)):
            Box(inner_x, c.groove_depth, c.groove_depth)

        # ── 3. Left arm top rail (additive) ───────────────────────────────
        # Protrudes groove_depth in +X from left arm inner face.
        left_inner_x = -(c.outer_x / 2 - c.wall)
        with Locations((left_inner_x + c.groove_depth / 2, -arm_y / 2, rail_cz)):
            Box(c.groove_depth, arm_y, c.groove_depth)

        # ── 4. Right arm top rail (additive) ──────────────────────────────
        right_inner_x = c.outer_x / 2 - c.wall
        with Locations((right_inner_x - c.groove_depth / 2, -arm_y / 2, rail_cz)):
            Box(c.groove_depth, arm_y, c.groove_depth)

        # ── 5. Flanges at open arm tips ────────────────────────────────────
        flange_cz = c.outer_z / 2
        flange_cy = -c.flange_thickness / 2

        # Left arm flange — outward in -X
        with Locations((-(c.outer_x / 2 + c.flange_width / 2), flange_cy, flange_cz)):
            Box(c.flange_width, c.flange_thickness, c.outer_z)

        # Right arm flange — outward in +X
        with Locations(((c.outer_x / 2 + c.flange_width / 2), flange_cy, flange_cz)):
            Box(c.flange_width, c.flange_thickness, c.outer_z)

        # ── 6. Small back tabs at outer tip of each main flange ────────────
        back_tab_cy = -(c.flange_thickness + c.flange_thickness / 2)

        back_tab_cx_l = -(c.outer_x / 2 + c.flange_width - c.flange_thickness / 2)
        with Locations((back_tab_cx_l, back_tab_cy, flange_cz)):
            Box(c.flange_thickness, c.flange_thickness, c.outer_z)

        back_tab_cx_r = c.outer_x / 2 + c.flange_width - c.flange_thickness / 2
        with Locations((back_tab_cx_r, back_tab_cy, flange_cz)):
            Box(c.flange_thickness, c.flange_thickness, c.outer_z)

    return wp.part


# ── Bottom panel ───────────────────────────────────────────────────────────────

def build_bottom(cfg: MoldConfig, *, convex_keys: bool, has_notch: bool) -> Part:
    """
    Sliding floor panel.

    Flat slab whose edges slide under the additive top rails of the wall pieces.
    Top edge is chamfered to guide the panel under the rail entry.

    convex_keys=True  → hemisphere bumps protrude up (Half A)
    convex_keys=False → hemispherical divots cut in (Half B)
    has_notch=True    → rectangular ID notch on one short edge (Half A only)
    """
    c = cfg

    # Panel fits between wall inner faces with clearance
    panel_x = c.outer_x - 2 * c.wall - c.tongue_clearance
    panel_y = c.outer_y - 2 * c.wall - c.tongue_clearance
    panel_h = c.groove_width - c.tongue_clearance
    chamfer_size = c.groove_depth / 2  # top edge bevel to guide under rail

    with BuildPart() as bp:

        # ── 1. Flat slab ──────────────────────────────────────────────────
        Box(panel_x, panel_y, panel_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        # ── 2. Chamfer top perimeter edge ─────────────────────────────────
        top_edges = bp.part.edges().group_by(Axis.Z)[-1]
        chamfer(top_edges, chamfer_size)

        # ── 3. Registration keys on top face ─────────────────────────────
        top_z = panel_h
        hemi_x = panel_x / 2 - c.hemi_offset
        hemi_y = panel_y / 2 - c.hemi_offset

        if convex_keys:
            hemi_cz = top_z - (c.hemi_r - c.hemi_height)
            with Locations(
                ( hemi_x,  hemi_y, hemi_cz),
                ( hemi_x, -hemi_y, hemi_cz),
                (-hemi_x,  hemi_y, hemi_cz),
                (-hemi_x, -hemi_y, hemi_cz),
            ):
                Sphere(c.hemi_r)
            # Clip sphere material below panel floor (z=0)
            with Locations((0, 0, -c.hemi_r / 2)):
                Box(panel_x + 2, panel_y + 2, c.hemi_r, mode=Mode.SUBTRACT)
            # Clip anything above top face level + hemi_height
            clip_above = top_z + c.hemi_height + 1
            with Locations((0, 0, clip_above)):
                Box(panel_x + 2, panel_y + 2, 2, mode=Mode.SUBTRACT)
        else:
            hemi_cz = top_z + (c.hemi_r - c.hemi_height)
            with Locations(
                ( hemi_x,  hemi_y, hemi_cz),
                ( hemi_x, -hemi_y, hemi_cz),
                (-hemi_x,  hemi_y, hemi_cz),
                (-hemi_x, -hemi_y, hemi_cz),
            ):
                Sphere(c.hemi_r, mode=Mode.SUBTRACT)

        # ── 4. ID notch on −Y short edge (Half A only) ────────────────────
        if has_notch:
            notch_cy = -(panel_y / 2 - c.notch_w / 2)
            notch_cz = top_z + c.notch_h / 2
            with Locations((0, notch_cy, notch_cz)):
                Box(c.notch_l, c.notch_w, c.notch_h)

    return bp.part


# ── Public builders ────────────────────────────────────────────────────────────

def build_half_a(cfg: MoldConfig) -> tuple[Part, Part, Part]:
    """Returns (wall_left, wall_right, bottom) for Half A."""
    wall = build_wall_piece(cfg)
    wall_r = mirror(wall, about=Plane.YZ)
    bottom = build_bottom(cfg, convex_keys=True, has_notch=True)
    return wall, wall_r, bottom


def build_half_b(cfg: MoldConfig) -> tuple[Part, Part, Part]:
    """Returns (wall_left, wall_right, bottom) for Half B."""
    wall = build_wall_piece(cfg)
    wall_r = mirror(wall, about=Plane.YZ)
    bottom = build_bottom(cfg, convex_keys=False, has_notch=False)
    return wall, wall_r, bottom


# ── Top-level generate ─────────────────────────────────────────────────────────

def generate(cfg: MoldConfig, printer: PrinterConfig):
    """
    Build all 6 mold pieces and warn if any exceeds the printer bed.
    Returns (wall_left_a, wall_right_a, bottom_a,
             wall_left_b, wall_right_b, bottom_b).
    """
    wla, wra, ba = build_half_a(cfg)
    wlb, wrb, bb = build_half_b(cfg)

    parts = [
        ("wall_left_a",  wla),
        ("wall_right_a", wra),
        ("bottom_a",     ba),
        ("wall_left_b",  wlb),
        ("wall_right_b", wrb),
        ("bottom_b",     bb),
    ]

    for label, part in parts:
        bb_box = part.bounding_box()
        sx = bb_box.max.X - bb_box.min.X
        sy = bb_box.max.Y - bb_box.min.Y
        sz = bb_box.max.Z - bb_box.min.Z
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

    return wla, wra, ba, wlb, wrb, bb
