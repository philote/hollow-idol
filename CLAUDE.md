# CLAUDE.md - hollow-idol - Parametric Mold Case Generator
Parametric mold case generator for ceramic slip casting. Generates build123d Python scripts that produce 3D-printable mold cases for tiki mugs and decorative ceramic forms.

## Workflow Context
1. AI tool (Tripo/Meshy) generates initial mesh from reference image
2. Mesh cleaned up in Nomad Sculpt (iPad) or Blender — must be watertight
3. hollow-idol generates a mold case sized around that mesh (or blank dims)
4. Case printed in PETG (FDM) or resin
5. Plaster poured into printed case around scaled model form
6. Plaster mold used for slip casting ceramic pieces
7. Fired ceramic shrinks ~13% (varies by clay body)

## 3D CAD Domain Rules
- This project involves parametric mold/case generation using build123d and CadQuery
- Keys go on the INTERIOR floor/flat surfaces of mold halves, NOT through exterior walls
- Notches are the receiving counterpart and must align with keys on the mating surface
- Always think in terms of: parting line, draft angles, interior cavity, exterior shell
- When unsure about 3D geometry placement, ASK before implementing

### Reference Images
- When the user provides a reference image (e.g., TinkerCAD screenshot), describe what you see in the image BACK to the user before writing code, to confirm shared understanding of the geometry

## Working Style
- Never run subagent/background commands without first explaining what you're about to do and why
- When performing multi-step operations, narrate each step before executing it
- If a task requires exploration, list the plan first and get approval

## Stack
- Python 3.11+
- build123d
- Output: STL and STEP
- Editor: VS Code

## CRITICAL — Development Approach
Build and verify geometry incrementally. Do not generate full architecture until each geometric primitive is confirmed working. The failure mode is generating plausible-looking code that produces incorrect geometry.

Order of operations:
1. Single mold half with correct parting face features — verify by user in PrusaSlicer
2. Matching second half with concave registration keys
3. Parametric config wrapping proven geometry
4. Full project structure, CLI, export pipeline
5. STL model import and boolean mode

Never refactor working geometry while adding new features without explicit permission from the user. If a solid exports cleanly and dimensions are correct, that code is frozen.

## Ceramic/Mold Domain Rules
- (optional) Masters scaled up by shrink_factor to account for clay shrinkage
- Default shrinkage: 13% (shrink_factor = 1.13) — parameterize per clay body
- Plaster walls minimum 25mm, ideally 30-40mm
- Registration keys on every parting face:
  - Convex hemispheres on one half
  - Matching concave divots on the other
  - Positioned on what will be the plaster the parting face (interior floor of the print model), not exterior walls
- Rectangular notch on one long side only for mold half identification

### Feature Definitions

- **Parting plane**: The flat plane where both plaster faces meet when assembled. 
- **Interior floor face**: The inner bottom surface of the tray cavity.
- **Keys**
  - **Convex key**: Hemisphere bump on the INTERIOR FLOOR FACE protruding INTO the cavity. Creates a concave impression in the plaster's parting surface.
  - **Concave key**: Hemispherical recess CUT INTO the INTERIOR FLOOR FACE. When plaster sets, fills with plaster creating a convex bump on the plaster's parting surface.
- **Chamfer**: 45° cut on the 4 outer vertical corners.

## Printer Configuration
- No hardcoded printer assumptions
- PrinterConfig dataclass: printer_name, bed_x, bed_y, bed_z
- Default build volume: 200 x 200 x 200mm
- Warn if any mold half exceeds configured build volume
- Common presets in printers.py

## Two Operating Modes
1. **Blank mode** — no STL, sized by manual width/height/depth inputs
2. **Model mode** — imports watertight STL, (optionally) scales by shrink_factor, booleans model out of mold cavity. This needs a lot more thought since 1/2 of the model should be on one printed mold and the other 1/2 in the other.

## Project Structure
hollow-idol/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── hollow_idol/
│   ├── __init__.py
│   ├── config.py        # MoldConfig + PrinterConfig dataclasses
│   ├── printers.py      # common printer presets
│   ├── mold_case.py     # main generator
│   ├── natches.py       # registration key geometry
│   ├── slip_well.py     # pour spout geometry
│   ├── split.py         # parting plane + mold half logic
│   └── export.py        # STL/STEP export, flat-lay arrangement
├── models/              # cleaned input STLs
├── output/              # exported mold half STLs
└── tests/

## Key Parameters (implement after geometry is verified)

### PrinterConfig
printer_name, bed_x, bed_y, bed_z

### MoldConfig
model_file, shrink_factor, wall_thickness,
split_axis, split_positions, num_parts,
natch_radius, natch_depth, natches_per_edge,
slip_well_diameter, slip_well_height,
draft_angle_deg, bounding_box_padding,
flange_width, flange_thickness