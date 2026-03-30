from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PrinterConfig:
    """Build volume and identity for a 3D printer."""

    printer_name: str = "generic"
    bed_x: float = 200.0  # mm
    bed_y: float = 200.0  # mm
    bed_z: float = 200.0  # mm


@dataclass
class MoldConfig:
    """Full parameter set for a mold case generation run."""

    # --- Input model ---
    model_file: Optional[str] = None
    shrink_factor: float = 1.13  # clay firing shrinkage multiplier (13% default)

    # --- Shell geometry ---
    wall_thickness: float = 30.0  # mm — minimum plaster wall mass
    draft_angle_deg: float = 3.0  # interior wall taper for demolding
    bounding_box_padding: float = 10.0  # extra space around imported model

    # --- Parting / split ---
    split_axis: str = "Z"  # axis the mold splits on
    split_positions: list[float] = field(default_factory=lambda: [0.0])
    num_parts: int = 2

    # --- Registration natches ---
    natch_radius: float = 6.0   # mm — hemisphere radius
    natch_depth: float = 3.0    # mm — how far the divot sinks (= radius for hemisphere)
    natches_per_edge: int = 2   # number of natches per parting face edge

    # --- Slip well ---
    slip_well_diameter: float = 40.0  # mm — pour hole diameter
    slip_well_height: float = 20.0    # mm — depth of pour funnel

    # --- Flange ---
    flange_width: float = 10.0      # mm — outward lip width for clamping
    flange_thickness: float = 5.0   # mm — flange height at parting plane

    # --- Blank mode dimensions ---
    blank_width: float = 100.0   # mm — interior cavity width (X)
    blank_depth: float = 100.0   # mm — interior cavity depth (Y)
    blank_height: float = 120.0  # mm — interior cavity height (Z)
