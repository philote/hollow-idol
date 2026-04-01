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
    notch_h: float = 5.0        # height above floor
