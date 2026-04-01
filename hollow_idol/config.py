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

    # --- Printed case wall ---
    case_wall: float = 8.0       # mm — printed plastic wall thickness; must be ≥ 2×natch_radius

    # --- Plaster sizing guidance (model mode) ---
    plaster_wall_min: float = 30.0   # mm — minimum plaster wall from master surface to case interior
    draft_angle_deg: float = 3.0     # interior wall taper for easy plaster release
    bounding_box_padding: float = 10.0  # extra space around imported model

    # --- Parting / split ---
    split_axis: str = "Y"  # axis the mold splits on ("Y" = front/back, "Z" = top/bottom)
    split_positions: list[float] = field(default_factory=lambda: [0.0])
    num_parts: int = 2

    # --- Registration natches ---
    natch_radius: float = 4.0   # mm — hemisphere radius; must be ≤ case_wall/2
    natch_depth: float = 3.0    # mm — how far the divot sinks (= radius for hemisphere)
    natches_per_edge: int = 2   # number of natches per parting face edge

    # --- Slip well (model mode only) ---
    slip_well_diameter: float = 40.0  # mm — pour hole diameter
    slip_well_height: float = 20.0    # mm — depth of pour funnel

    # --- Clamping clips ---
    clip_width: float = 15.0    # mm — clip tab width (along parting edge)
    clip_height: float = 10.0   # mm — clip tab height (Z)
    clip_depth: float = 6.0     # mm — how far the clip protrudes from the case wall

    # --- Exterior finish ---
    chamfer_size: float = 3.0           # mm — chamfer on the 4 outer vertical edges
    orientation_notch_size: float = 8.0 # mm — width/depth of asymmetric notch tab on -Z exterior wall

    # --- Blank mode dimensions ---
    blank_width: float = 100.0   # mm — interior cavity width (X)
    blank_depth: float = 100.0   # mm — interior cavity total depth (Y); each half gets blank_depth/2
    blank_height: float = 120.0  # mm — interior cavity height (Z)
