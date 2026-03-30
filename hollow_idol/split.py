"""Parting plane logic and mold-half separation.

Splits an assembled mold block into halves (or thirds) by intersecting it
with large cutter boxes at each split position.
"""
from __future__ import annotations

import cadquery as cq

from hollow_idol.config import MoldConfig

# Size of the cutter boxes — large enough to cover any realistic mold
_BIG = 2000.0


def split_mold(
    assembled: cq.Workplane,
    cfg: MoldConfig,
) -> list[cq.Workplane]:
    """Split an assembled mold block into halves along the configured axis.

    Currently supports Z-axis splits only (split_axis = "Z").

    For a two-part mold with split_positions=[0.0]:
        - halves[0]: bottom half (Z ≤ 0)
        - halves[1]: top half (Z ≥ 0)

    Args:
        assembled:  The full mold block (including flange) centred at origin.
        cfg:        MoldConfig — split_axis, split_positions, num_parts.

    Returns:
        List of mold half Workplanes, bottom to top.
    """
    if cfg.split_axis != "Z":
        raise NotImplementedError(
            f"split_axis={cfg.split_axis!r} is not yet supported; only 'Z' is implemented."
        )

    positions = sorted(cfg.split_positions)

    # Build Z boundaries: -∞, pos0, pos1, ..., +∞
    boundaries = [-_BIG] + positions + [_BIG]

    halves: list[cq.Workplane] = []
    for i in range(len(boundaries) - 1):
        z_lo = boundaries[i]
        z_hi = boundaries[i + 1]
        cutter = _z_slab(z_lo, z_hi)
        half = assembled.intersect(cutter)
        halves.append(half)

    return halves


def _z_slab(z_lo: float, z_hi: float) -> cq.Workplane:
    """Axis-aligned box spanning [z_lo, z_hi] in Z, unlimited in X/Y."""
    height = z_hi - z_lo
    centre_z = (z_lo + z_hi) / 2.0
    return (
        cq.Workplane("XY")
        .box(_BIG, _BIG, height, centered=True)
        .translate((0.0, 0.0, centre_z))
    )
