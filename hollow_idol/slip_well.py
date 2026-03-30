"""Slip well (pour spout) geometry.

The slip well is a cylindrical or slightly tapered funnel cut into the top
of the top mold half.  Liquid clay is poured through it to fill the mold
cavity.
"""
from __future__ import annotations

import cadquery as cq

from hollow_idol.config import MoldConfig


def add_slip_well(
    solid: cq.Workplane,
    cfg: MoldConfig,
    top_z: float,
) -> cq.Workplane:
    """Cut a slip well into the top of the given solid.

    The well is centred at (0, 0) and descends from the top face of the mold.
    When draft_angle_deg > 0 the well is slightly tapered (wider at the top)
    to make it easier to pour and to clean.

    Args:
        solid:  The top mold half.
        cfg:    MoldConfig — slip_well_diameter, slip_well_height, draft_angle_deg.
        top_z:  Z coordinate of the top face of the solid.

    Returns:
        Solid with the slip well cut out.
    """
    import math

    r_top = cfg.slip_well_diameter / 2.0
    h = cfg.slip_well_height

    if cfg.draft_angle_deg > 0:
        # Taper: bottom of well is narrower than top (easier pour + demolding)
        taper = h * math.tan(math.radians(cfg.draft_angle_deg))
        r_bottom = max(r_top - taper, r_top * 0.5)

        # Loft between top circle and smaller bottom circle
        well_cutter = (
            cq.Workplane("XY")
            .workplane(offset=top_z)
            .circle(r_top)
            .workplane(offset=-h)
            .circle(r_bottom)
            .loft()
        )
    else:
        well_cutter = (
            cq.Workplane("XY")
            .workplane(offset=top_z)
            .circle(r_top)
            .extrude(-h)
        )

    return solid.cut(well_cutter)
