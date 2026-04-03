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

        back_inner_y = -(c.outer_y / 2 - c.wall)
        left_inner_x  = -(c.outer_x / 2 - c.wall)
        right_inner_x =  (c.outer_x / 2 - c.wall)

        # ── Interior corner chamfers ───────────────────────────────────────
        # Fill the 2 concave vertical corners where each arm's inner face
        # meets the back wall's inner face with a right-triangle prism.
        # Left corner: right angle at (left_inner_x, back_inner_y), fills +X/+Y
        with BuildSketch(Plane.XY) as sk_lc:
            with BuildLine():
                Polyline(
                    (left_inner_x,              back_inner_y),
                    (left_inner_x + c.chamfer,  back_inner_y),
                    (left_inner_x,              back_inner_y + c.chamfer),
                    close=True,
                )
            make_face()
        extrude(sk_lc.sketch, amount=c.outer_z)

        # Right corner: right angle at (right_inner_x, back_inner_y), fills -X/+Y
        with BuildSketch(Plane.XY) as sk_rc:
            with BuildLine():
                Polyline(
                    (right_inner_x,             back_inner_y),
                    (right_inner_x - c.chamfer, back_inner_y),
                    (right_inner_x,             back_inner_y + c.chamfer),
                    close=True,
                )
            make_face()
        extrude(sk_rc.sketch, amount=c.outer_z)

        # ── 2-4. Bottom ledges on all 3 inner wall faces ───────────────────
        # Panel rests on top of these (ledge top face at Z = groove_depth).
        ledge_cz = c.groove_depth / 2
        with Locations((0, back_inner_y + c.groove_depth / 2, ledge_cz)):
            Box(inner_x, c.groove_depth, c.groove_depth)
        with Locations((left_inner_x + c.groove_depth / 2, -arm_y / 2, ledge_cz)):
            Box(c.groove_depth, arm_y, c.groove_depth)
        with Locations((right_inner_x - c.groove_depth / 2, -arm_y / 2, ledge_cz)):
            Box(c.groove_depth, arm_y, c.groove_depth)

        # ── 5-7. Top rails on all 3 inner wall faces (triangular prism) ───
        # Right-triangle cross-section mates with the chamfered top edge of the
        # bottom panel. Right angle at the wall-face top corner; 45° hypotenuse
        # faces the groove opening.
        z_bot_rail = c.groove_depth + c.groove_width
        z_top_rail = z_bot_rail + c.groove_depth
        z_mid_rail = z_bot_rail + c.groove_depth / 2  # apex of symmetric wedge
        rail_reach = c.groove_depth / 2               # horizontal extent to apex

        # Back wall rail — symmetric wedge in Y-Z plane, extruded along X
        with BuildSketch(Plane.YZ) as sk_back_rail:
            with BuildLine():
                Polyline(
                    (back_inner_y,                z_bot_rail),
                    (back_inner_y,                z_top_rail),
                    (back_inner_y + rail_reach,   z_mid_rail),
                    close=True,
                )
            make_face()
        extrude(sk_back_rail.sketch, amount=inner_x / 2, both=True)

        # Arm rails — symmetric wedge in X-Z plane, extruded along -Y into each arm.
        arm_plane = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))

        # Left arm: inner face at left_inner_x, apex toward +X (centre)
        with BuildSketch(arm_plane) as sk_left_rail:
            with BuildLine():
                Polyline(
                    (left_inner_x,               z_bot_rail),
                    (left_inner_x,               z_top_rail),
                    (left_inner_x + rail_reach,  z_mid_rail),
                    close=True,
                )
            make_face()
        extrude(sk_left_rail.sketch, amount=arm_y)

        # Right arm: inner face at right_inner_x, apex toward -X (centre)
        with BuildSketch(arm_plane) as sk_right_rail:
            with BuildLine():
                Polyline(
                    (right_inner_x,              z_bot_rail),
                    (right_inner_x,              z_top_rail),
                    (right_inner_x - rail_reach, z_mid_rail),
                    close=True,
                )
            make_face()
        extrude(sk_right_rail.sketch, amount=arm_y)

        # ── 9. Flanges at open arm tips ────────────────────────────────────
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
            # Chamfer bottom corners of notch (where notch meets panel top face)
            # so notch slides past arm rail entry without snagging.
            try:
                notch_base_edges = [
                    e for e in bp.part.edges()
                    if (abs(e.center().Z - top_z) < 0.5
                        and (abs(e.center().Y - (notch_cy + c.notch_w / 2)) < 0.5
                             or abs(e.center().Y - (notch_cy - c.notch_w / 2)) < 0.5)
                        and abs(e.length - c.notch_l) < 1.0)
                ]
                if notch_base_edges:
                    chamfer(notch_base_edges, min(c.notch_w / 3, 2.0))
            except Exception:
                pass

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
