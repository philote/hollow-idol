from dataclasses import dataclass


@dataclass
class PrinterConfig:
    printer_name: str
    bed_x: float
    bed_y: float
    bed_z: float


@dataclass
class MoldConfig:
    # Outer tray dimensions
    outer_x: float = 100.0
    outer_y: float = 80.0
    outer_z: float = 40.0

    # Shell
    wall: float = 5.0           # wall + floor thickness

    # Interior edge chamfer
    chamfer: float = 3.0

    # Registration keys (hemispheres)
    hemi_r: float = 6.0         # sphere radius
    hemi_height: float = 3.0    # dome/divot height (must be < hemi_r)
    hemi_offset: float = 15.0   # distance from interior corner to key centre

    # Identification notch (Half A only, one long side)
    notch_l: float = 10.0       # length along wall
    notch_w: float = 5.0        # width into cavity
    notch_h: float = 10.0       # protrusion height above panel face

    # Groove-and-tongue joint (wall pieces ↔ bottom panel)
    groove_depth: float = 4.0        # groove depth into wall (= tongue depth)
    groove_width: float = 5.0        # groove slot width
    tongue_clearance: float = 0.25   # fit clearance: tongue is this much narrower than groove

    # Flanges for binder clips (at arm-tip mating faces)
    flange_width: float = 10.0       # clip grip surface width
    flange_thickness: float = 3.0    # flange plate thickness
