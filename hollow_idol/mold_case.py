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

    The groove runs along the bottom inner edge of all three walls (U-path),
    forming the track the bottom panel slides into.
    Flanges project outward from the open arm-tip faces.

    Mirror in X to get the `]` piece.
    """
    c = cfg

    # Half the short dimension — each arm extends this far inward
    arm_y = c.outer_y / 2

    # ── 1. Long outer wall (full X width, arm_y deep, full Z tall) ──────────
    with BuildPart() as wp:

        # Long wall slab — wall-thick only, sits at the back (−Y)
        with Locations((0, -(c.outer_y / 2 - c.wall / 2), c.outer_z / 2)):
            Box(c.outer_x, c.wall, c.outer_z)

        # Left arm (−X end) — same half as the long wall, extending to the opening
        with Locations((-(c.outer_x / 2 - c.wall / 2), -arm_y / 2, c.outer_z / 2)):
            Box(c.wall, arm_y, c.outer_z)

        # Right arm (+X end)
        with Locations(((c.outer_x / 2 - c.wall / 2), -arm_y / 2, c.outer_z / 2)):
            Box(c.wall, arm_y, c.outer_z)

        # ── 2. Hollow interior of long wall (leave wall thickness on three sides) ──
        inner_x = c.outer_x - 2 * c.wall
        hollow_y = arm_y - c.wall  # interior depth of long-wall cavity
        with Locations((0, -(c.outer_y / 2 - arm_y / 2) + c.wall / 2,
                         c.wall + hollow_y / 2 + c.groove_width)):
            # subtract interior above the groove level
            interior_z = c.outer_z - c.wall - c.groove_width
            Box(inner_x, hollow_y, interior_z, mode=Mode.SUBTRACT)

        # ── 3. Groove channel along bottom inner edge of long wall ──────────
        # Rectangular slot: groove_width tall, groove_depth into the wall
        groove_cz = c.wall + c.groove_width / 2
        groove_cy = -(c.outer_y / 2 - c.wall / 2)  # inner face of long wall
        with Locations((0, groove_cy - c.groove_depth / 2, groove_cz)):
            Box(inner_x, c.groove_depth, c.groove_width, mode=Mode.SUBTRACT)

        # ── 4. Groove channel along bottom inner edge of left arm ──────────
        arm_inner_x = -(c.outer_x / 2 - c.wall)  # inner face of left arm
        arm_inner_y = arm_y - c.wall / 2
        # groove runs in Y direction along left arm interior face
        with Locations((arm_inner_x - c.groove_depth / 2, arm_inner_y / 2, groove_cz)):
            Box(c.groove_depth, arm_inner_y, c.groove_width, mode=Mode.SUBTRACT)

        # ── 5. Groove channel along bottom inner edge of right arm ─────────
        arm_inner_x_r = c.outer_x / 2 - c.wall
        with Locations((arm_inner_x_r + c.groove_depth / 2, arm_inner_y / 2, groove_cz)):
            Box(c.groove_depth, arm_inner_y, c.groove_width, mode=Mode.SUBTRACT)

        # ── 6. Flanges at open arm tips ────────────────────────────────────
        # Flange tabs project outward (+Y) from each arm tip
        flange_cz = c.outer_z / 2
        # Flanges stick outward in X from the arm outer face, at the arm open tip (Y=0).
        # This creates a corner ledge binder clips grip when clamping in Y.
        flange_cy = -c.flange_thickness / 2  # centred on Y=0, within arm tip

        # Left arm flange — outward in -X from arm outer face at X=-outer_x/2
        with Locations((-(c.outer_x / 2 + c.flange_width / 2), flange_cy, flange_cz)):
            Box(c.flange_width, c.flange_thickness, c.outer_z)

        # Right arm flange — outward in +X
        with Locations(((c.outer_x / 2 + c.flange_width / 2), flange_cy, flange_cz)):
            Box(c.flange_width, c.flange_thickness, c.outer_z)

    return wp.part


# ── Bottom panel ───────────────────────────────────────────────────────────────

def build_bottom(cfg: MoldConfig, *, convex_keys: bool, has_notch: bool) -> Part:
    """
    Sliding floor panel.

    The tongue (thin lip) around all 4 edges fits into the U-groove of each
    wall piece. Panel slides in along the short-arm grooves until the leading
    edge seats against the long-wall groove stop.

    convex_keys=True  → hemisphere bumps protrude up (Half A — creates concave
                         impression in plaster parting face)
    convex_keys=False → hemispherical divots cut in (Half B)
    has_notch=True    → rectangular ID notch on one short edge (Half A only)
    """
    c = cfg

    tongue_t = c.groove_width - c.tongue_clearance   # tongue thickness (Z)
    tongue_d = c.groove_depth - c.tongue_clearance   # tongue width into groove

    # Panel outer footprint: fits inside assembled groove slot
    panel_x = c.outer_x - 2 * c.wall + 2 * tongue_d - c.tongue_clearance
    panel_y = c.outer_y - 2 * c.wall + 2 * tongue_d - c.tongue_clearance

    # Panel body thickness (above the tongue ledge)
    body_t = c.wall - tongue_t  # total panel height = wall thickness

    inner_x = panel_x - 2 * tongue_d   # exposed interior face size
    inner_y = panel_y - 2 * tongue_d

    with BuildPart() as bp:

        # ── 1. Full panel base (tongue level) ────────────────────────────
        Box(panel_x, panel_y, tongue_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        # ── 2. Inner body raised above tongue ────────────────────────────
        with Locations((0, 0, tongue_t)):
            Box(inner_x, inner_y, body_t,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # ── 3. Registration keys on top face ─────────────────────────────
        top_z = tongue_t + body_t
        hemi_x = inner_x / 2 - c.hemi_offset
        hemi_y = inner_y / 2 - c.hemi_offset

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
        # Convex bump on top face → leaves a concave gap in plaster parting
        # face, letting a tool be wedged in to pry the plaster halves apart.
        if has_notch:
            notch_cy = -(inner_y / 2 - c.notch_w / 2)
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
