# CLAUDE.md - Parametric Mold Case Generator
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose
**hollow-idol** Parametric mold case generator for ceramic slip casting. Cases are printed in 3D filament or resin, filled with plaster to create slip casting molds for ceramic production (primarily tiki mugs and decorative forms).


## Workflow Context
1. AI tool (Tripo/Meshy) generates initial mesh from reference image
2. Mesh cleaned up in Nomad Sculpt (iPad) or Blender — must be watertight
3. hollow-idol generates a mold case sized around that mesh (or blank dims)
4. Case printed in PETG (FDM) or resin
5. Plaster poured into printed case around scaled model form
6. Plaster mold used for slip casting ceramic pieces
7. Fired ceramic shrinks ~13% (varies by clay body)

## Stack
- Python 3.11+
- CadQuery 2.x
- Output: STL and STEP
- Editor: VS Code

## Ceramic/Mold Domain Rules
- Masters scaled up by shrink_factor to account for clay shrinkage
- Default shrinkage: 13% (shrink_factor = 1.13) — parameterize per clay body
- Plaster walls minimum 25mm, ideally 30-40mm
- Draft angles minimum 3° on all interior walls — use CadQuery native draft
- Registration natches on every parting face
- Slip well at top for pouring liquid clay (default 40mm diameter)
- Flange lip around parting edges for rubber band / clamp during casting
- 3-part molds needed for forms with undercuts (e.g. tiki faces, handles)

## CadQuery Conventions
- All units in mm
- Parameters isolated in MoldConfig + PrinterConfig dataclasses in config.py
- Each mold half is a separate CadQuery solid
- Full assembled solid for preview
- Flat-lay arrangement for print-ready export
- Graceful error handling around STL boolean operations
- Warn if any mold half exceeds configured build volume

## Two Operating Modes
1. **Model mode** — imports watertight STL, scales by shrink_factor,
   booleans model out of mold cavity
2. **Blank mode** — no STL, sized by manual width/height/depth inputs

## Project Structure
hollow-idol/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── hollow_idol/
│   ├── __init__.py
│   ├── config.py        # MoldConfig + PrinterConfig dataclasses + defaults
│   ├── printers.py      # common printer presets
│   ├── mold_case.py     # main generator
│   ├── natches.py       # registration key geometry
│   ├── slip_well.py     # pour spout geometry
│   ├── split.py         # parting plane + mold half logic
│   └── export.py        # STL/STEP export, flat-lay arrangement
├── models/              # cleaned input STLs
├── output/              # exported mold half STLs
└── tests/

## Mold Case Terminology

**BEFORE WRITING ANY GEOMETRY CODE:** Read `docs/example_target_mold.png` with the Read tool.
It shows exactly where features go. Do not reason about coordinates without looking at it first.

Reference images:
- `docs/example_target_mold.png` — labeled Tinkercad mockup showing correct geometry
- `docs/bug_original_floating_natches.png` — example of the wrong output (floating natches bug)

### Coordinate System

```
Front half (design coords):
  X — width   (cavity spans ±blank_width/2)
  Y — depth   (floor at -(blank_depth/2 + case_wall), open face at Y=0)
  Z — height  (cavity spans ±blank_height/2)

Back half = front half mirrored over XZ plane (Y → -Y):
  floor at +(blank_depth/2 + case_wall), open face at Y=0
```

### Feature Definitions

- **Parting plane**: Y=0. The flat plane where both open faces meet when assembled. NO features live here.
- **Interior floor face**: The inner bottom surface of the tray cavity.
  - Front half: Y = -blank_depth/2 (e.g. -50mm for blank_depth=100)
  - Back half: Y = +blank_depth/2 (e.g. +50mm, after mirroring)
- **Convex key**: Hemisphere bump on the INTERIOR FLOOR FACE protruding INTO the cavity (+Y direction). Front half only. When plaster sets, creates a concave impression in the plaster's parting surface.
- **Concave key**: Hemispherical recess CUT INTO the floor solid material (+Y direction into Y > floor_y). Back half only. When plaster sets, fills with plaster creating a convex bump on the back plaster's parting surface.
- **Key constraint (CRITICAL)**: `natch_radius ≤ case_wall / 2` — otherwise the concave key punches through the floor. Defaults: natch_radius=4, case_wall=8 (4 ≤ 4 ✓).
- **Key positions**: Within cavity footprint, inset from walls by `natch_radius + 2mm`. NOT on the outer wall rim or flange.
- **Orientation notch**: Small rectangular tab on ONE exterior side wall only (-Z wall). Same position on both halves — makes the assembled shape asymmetric so you can't assemble backwards.
- **Chamfer**: 45° cut on the 4 outer vertical edges (corners parallel to Y). Applied via `.edges("|Y").chamfer(size)`.
- **Flange area**: Wall cross-section ring visible at Y=0. Keys do NOT go here — they go on the interior floor.

## Key Parameters

### PrinterConfig
printer_name, bed_x, bed_y, bed_z

### MoldConfig
model_file, shrink_factor, wall_thickness,
split_axis, split_positions, num_parts,
natch_radius, natch_depth, natches_per_edge,
slip_well_diameter, slip_well_height,
draft_angle_deg, bounding_box_padding,
flange_width, flange_thickness