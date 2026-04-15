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

    # Registration keys
    key_count: int = 4          # supported layouts: 1-6 keys
    key_radius: float = 6.0     # sphere radius
    key_height: float = 3.0     # dome/divot height (must be < key_radius)
    key_offset: float = 15.0    # distance from panel edge to outer key centres

    # Identification notch (Half A only, one long side)
    notch_l: float = 10.0       # length along wall
    notch_w: float = 5.0        # width into cavity
    notch_h: float = 10.0       # protrusion height above panel face

    # Sliding panel fit
    tongue_clearance: float = 0.25   # fit clearance between panel and wall opening

    # Flanges for binder clips (at arm-tip mating faces)
    flange_width: float = 10.0       # clip grip surface width
    flange_thickness: float = 3.0    # flange plate thickness

    def __post_init__(self) -> None:
        if not 1 <= self.key_count <= 6:
            raise ValueError(f"key_count must be between 1 and 6, got {self.key_count}")
        if self.key_height >= self.key_radius:
            raise ValueError(
                f"key_height must be less than key_radius, got {self.key_height} >= {self.key_radius}"
            )
