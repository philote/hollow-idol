"""Registration key geometry — placed on the INTERIOR FLOOR FACE of each mold half.

See docs/example_target_mold.png for the visual reference.  Read it before
editing this file.

What the example shows:
    Front half (pink): 4 dome bumps on the interior floor, pointing UP into the
        cavity.  These create concave impressions in the plaster.
    Back half (red):   4 hemispherical recesses cut INTO the floor material.
        Plaster fills them and hardens into convex bumps.
    When the two plaster halves are assembled, concave ↔ convex → aligned.

Coordinate system (design space, before flat-lay rotation):
    Front half interior at Y < 0, floor solid at Y ∈ [-(depth/2+wall), -depth/2].
    Interior floor face at Y = -blank_depth/2.

    Back half is front mirrored over XZ (Y → -Y):
    Interior at Y > 0, floor solid at Y ∈ [+depth/2, +(depth/2+wall)].
    Interior floor face at Y = +blank_depth/2.

Key hemisphere direction: always +Y (flat base toward open face, apex away).
    Front (mode="bump"):  translate to (x, -depth/2, z) → body at Y∈[-50,-46]
                          protrudes INTO cavity ✓
    Back  (mode="divot"): translate to (x, +depth/2, z) → body at Y∈[+50,+54]
                          cuts INTO floor solid ✓ (requires natch_radius ≤ case_wall/2)

Key positions are within the cavity footprint, inset from each wall by
natch_radius + 2mm to keep the hemisphere fully inside the cavity bounds.
"""
from __future__ import annotations

import cadquery as cq

from hollow_idol.config import MoldConfig

_BIG = 2000.0


def _make_floor_key(radius: float) -> cq.Workplane:
    """Hemisphere: flat base at Y=0, apex at Y=+radius.

    Translate to (x, floor_y, z) before use.  Same template used for both
    convex (union) and concave (cut) operations.

    Args:
        radius: Hemisphere radius in mm.

    Returns:
        Hemisphere solid with flat base on XZ plane (Y=0), apex at Y=+radius.
    """
    sphere = cq.Workplane("XY").sphere(radius)
    # Cut away everything at Y < 0 → only +Y hemisphere remains.
    neg_y_cutter = (
        cq.Workplane("XY")
        .box(_BIG, _BIG, _BIG, centered=True)
        .translate((0.0, -_BIG / 2.0, 0.0))
    )
    return sphere.cut(neg_y_cutter)


def _key_positions(cfg: MoldConfig) -> list[tuple[float, float]]:
    """Compute (x, z) positions for all registration keys.

    Keys are placed within the cavity footprint, inset from each wall by
    natch_radius + 2mm.  An endpoint-inclusive spread is used so that
    natches_per_edge=2 places one key near each end of the long axis —
    producing 4 corner-region keys total, matching the reference image.

    Returns:
        List of (x, z) pairs.  All keys share the same floor_y; caller
        supplies floor_y when translating.
    """
    hw = cfg.blank_width / 2.0
    hh = cfg.blank_height / 2.0
    r = cfg.natch_radius
    margin = 2.0
    n = cfg.natches_per_edge

    # Inset from each cavity wall so the hemisphere stays entirely inside.
    x_inner = hw - r - margin   # e.g. 50-4-2 = 44 mm
    z_inner = hh - r - margin   # e.g. 60-4-2 = 54 mm

    # Clamp in case cavity is too small.
    x_inner = max(x_inner, 0.0)
    z_inner = max(z_inner, 0.0)

    def _linspace_endpoints(lo: float, hi: float, count: int) -> list[float]:
        """count=1 → midpoint; count=2 → [lo, hi]; count=3 → [lo, mid, hi]."""
        if count == 1:
            return [(lo + hi) / 2.0]
        step = (hi - lo) / (count - 1)
        return [lo + step * i for i in range(count)]

    positions: list[tuple[float, float]] = []

    # Two columns at ±x_inner, rows spread along Z.
    for z in _linspace_endpoints(-z_inner, z_inner, n):
        positions.append((x_inner, z))
        positions.append((-x_inner, z))

    return positions


def apply_natches(
    solid: cq.Workplane,
    cfg: MoldConfig,
    mode: str,
    floor_y: float,
) -> cq.Workplane:
    """Add registration keys to the interior floor face of a mold half.

    Args:
        solid:   Mold half to modify.
        cfg:     MoldConfig — natch_radius, natches_per_edge, blank dims.
        mode:    "bump"  → union hemispheres onto floor (front half, convex keys)
                 "divot" → cut hemispheres into floor solid (back half, concave keys)
        floor_y: Y coordinate of the interior floor face.
                 Front half: -blank_depth/2
                 Back half:  +blank_depth/2

    Returns:
        Modified solid with registration keys applied.
    """
    if mode not in ("bump", "divot"):
        raise ValueError(f"mode must be 'bump' or 'divot', got {mode!r}")

    key_template = _make_floor_key(cfg.natch_radius)

    for (x, z) in _key_positions(cfg):
        key = key_template.translate((x, floor_y, z))
        if mode == "bump":
            solid = solid.union(key)
        else:
            solid = solid.cut(key)

    return solid
