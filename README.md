# hollow-idol

Parametric mold case generator for ceramic slip casting.

Generates 3D-printable mold cases (shells) that are filled with plaster to create slip casting molds. Designed for tiki mugs, decorative forms, and any piece requiring multi-part plaster molds.

---

## Requirements

- **Python 3.11+**
- **CadQuery 2.4+** — requires the OCP/Open CASCADE geometry kernel
- pip or [uv](https://github.com/astral-sh/uv)

> **Note on CadQuery install**: CadQuery bundles a pre-built OCP wheel. On most platforms `pip install cadquery` works directly. If you hit issues, see the [CadQuery install guide](https://cadquery.readthedocs.io/en/latest/installation.html).

---

## Install

**With pip (standard):**
```bash
pip install -e ".[dev]"
```

**With uv (faster):**
```bash
uv sync
```

**Or via Make:**
```bash
make install
```

---

## Usage

### Blank mode — box cavity, no mesh required

```python
from hollow_idol.config import MoldConfig, PrinterConfig
from hollow_idol.mold_case import build_blank_mold
from hollow_idol.export import export_mold
from hollow_idol.printers import get_printer

printer = get_printer("bambu_x1c")

cfg = MoldConfig(
    blank_width=100,    # mm — interior cavity
    blank_depth=80,
    blank_height=120,
    wall_thickness=30,
    draft_angle_deg=3,
)

result = build_blank_mold(cfg, printer)
export_mold(result, output_dir="output", base_name="my_mold", printer=printer)
```

Outputs:
- `output/my_mold_half_0.stl` — bottom half, flat-lay oriented for printing
- `output/my_mold_half_1.stl` — top half
- `output/my_mold_assembled.step` — full assembly for preview
- `output/my_mold_assembled.stl`

### Run the example

```bash
make example
```

### Run tests

```bash
make test
# or
pytest
```

---

## Printer presets

| Key | Printer | Bed X | Bed Y | Bed Z |
|---|---|---|---|---|
| `bambu_x1c` | Bambu Lab X1C | 256 | 256 | 256 |
| `bambu_p1s` | Bambu Lab P1S | 256 | 256 | 256 |
| `bambu_a1` | Bambu Lab A1 | 256 | 256 | 256 |
| `prusa_mk4` | Prusa MK4 | 250 | 210 | 220 |
| `prusa_xl` | Prusa XL | 360 | 360 | 360 |
| `creality_ender3` | Creality Ender 3 | 220 | 220 | 250 |
| `creality_k1` | Creality K1 | 220 | 220 | 250 |
| `voron_2_4` | Voron 2.4 (300mm) | 300 | 300 | 280 |
| `elegoo_saturn3` | Elegoo Saturn 3 Ultra | 218 | 123 | 260 |
| `phrozen_mega8k` | Phrozen Mega 8K | 218 | 123 | 235 |
| `generic` | Generic | 200 | 200 | 200 |

Override any field:
```python
printer = get_printer("prusa_mk4", bed_z=300)
```

Use a custom printer not in the list:
```python
from hollow_idol.config import PrinterConfig
printer = PrinterConfig(printer_name="My Printer", bed_x=350, bed_y=350, bed_z=400)
```

---

## Key MoldConfig parameters

| Parameter | Default | Description |
|---|---|---|
| `blank_width` | 100 mm | Interior cavity width (X) |
| `blank_depth` | 100 mm | Interior cavity depth (Y) |
| `blank_height` | 120 mm | Interior cavity height (Z) |
| `wall_thickness` | 30 mm | Plaster wall mass (min 25 mm recommended) |
| `shrink_factor` | 1.13 | Clay firing shrinkage multiplier (13% default) |
| `draft_angle_deg` | 3° | Interior wall taper for demolding |
| `num_parts` | 2 | Mold halves (2-part split) |
| `natch_radius` | 6 mm | Registration hemisphere radius |
| `natches_per_edge` | 2 | Natches placed per parting face edge |
| `slip_well_diameter` | 40 mm | Pour hole diameter |
| `flange_width` | 10 mm | Clamping lip width |

---

## cq-editor preview

Open `hollow_idol/mold_case.py` directly in [cq-editor](https://github.com/CadQuery/CQ-editor) for live 3D preview. Add a `show_object()` call at the bottom for each solid you want to visualise:

```python
# At end of mold_case.py for cq-editor:
from hollow_idol.config import MoldConfig, PrinterConfig
result = build_blank_mold(MoldConfig(), PrinterConfig())
show_object(result["assembled"], name="assembled")
show_object(result["halves"][0], name="bottom_half")
show_object(result["halves"][1], name="top_half")
```

---

## Workflow

1. AI tool (Tripo/Meshy) generates mesh from reference image
2. Mesh cleaned up in Nomad Sculpt or Blender — must be watertight
3. hollow-idol generates a mold case sized around that mesh (or blank dims)
4. Case printed in PETG (FDM) or resin
5. Plaster poured into printed case around scaled model form
6. Plaster mold used for slip casting ceramic pieces
7. Fired ceramic shrinks ~13% (varies by clay body)
