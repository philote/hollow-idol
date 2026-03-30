"""Registration natch geometry.

Natches are hemisphere bumps and matching divots placed on parting faces
to align mold halves during assembly.

Convention:
- Parting plane is at Z=0
- Bumps protrude in the +Z direction (above the parting face of the bottom half)
- Divots are cut in the +Z direction (into the bottom face of the top half)
- Both shapes are identical upper hemispheres; bump = union, divot = cut
"""
from __future__ import annotations

import math

import cadquery as cq

from hollow_idol.config import MoldConfig


def make_natch_bump(radius: float) -> cq.Workplane:
    """Upper hemisphere solid.  Base at Z=0, apex at Z=+radius."""
    BIG = radius * 20
    sphere = cq.Workplane("XY").sphere(radius)
    # Cut away the lower hemisphere (Z < 0)
    lower_half = (
        cq.Workplane("XY")
        .box(BIG, BIG, BIG, centered=True)
        .translate((0.0, 0.0, -BIG / 2.0))
    )
    return sphere.cut(lower_half)


def _natch_positions(cfg: MoldConfig) -> list[tuple[float, float]]:
    """Compute (x, y) positions for natches on the Z=0 parting face.

    Natches are placed at the midpoint of each wall segment, symmetrically
    spaced along each of the 4 sides.
    """
    hw = cfg.blank_width / 2.0
    hd = cfg.blank_depth / 2.0
    wt = cfg.wall_thickness
    n = cfg.natches_per_edge

    # Radial distance from cavity face to natch centre = half wall thickness
    wall_mid = wt / 2.0

    positions: list[tuple[float, float]] = []

    # Evenly space n natches along each edge direction
    def _linspace(lo: float, hi: float, count: int) -> list[float]:
        if count == 1:
            return [(lo + hi) / 2.0]
        step = (hi - lo) / (count + 1)
        return [lo + step * (i + 1) for i in range(count)]

    ys = _linspace(-hd, hd, n)
    xs = _linspace(-hw, hw, n)

    for y in ys:
        positions.append((hw + wall_mid, y))    # +X wall
        positions.append((-hw - wall_mid, y))   # -X wall

    for x in xs:
        positions.append((x, hd + wall_mid))    # +Y wall
        positions.append((x, -hd - wall_mid))   # -Y wall

    return positions


def apply_natches(
    solid: cq.Workplane,
    cfg: MoldConfig,
    mode: str,
) -> cq.Workplane:
    """Add registration natches to a mold half at the Z=0 parting plane.

    Args:
        solid:  The mold half to modify.
        cfg:    MoldConfig — used for natch sizing and positions.
        mode:   "bump"  → union hemispheres onto the solid (bottom half)
                "divot" → cut hemispheres into the solid (top half)

    Returns:
        Modified solid with natches applied.
    """
    if mode not in ("bump", "divot"):
        raise ValueError(f"mode must be 'bump' or 'divot', got {mode!r}")

    positions = _natch_positions(cfg)
    natch = make_natch_bump(cfg.natch_radius)

    for x, y in positions:
        natch_placed = natch.translate((x, y, 0.0))
        if mode == "bump":
            solid = solid.union(natch_placed)
        else:
            solid = solid.cut(natch_placed)

    return solid
