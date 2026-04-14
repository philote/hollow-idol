# hollow-idol

Parametric mold case generator for ceramic slip casting. Given outer dimensions, generates 6 3D-printable STL pieces: two C-frame wall pieces (mirrored) and two sliding bottom panels — one half with convex registration keys, one with concave divots. Print in PETG, pour plaster into the assembled case, use the resulting plaster mold for slip casting.

---

## Setup

**Requires Python 3.10–3.12.** The `build123d` dependency relies on `cadquery-ocp`, which only has pre-built wheels for these versions. Python 3.13+ is not yet supported.

### macOS (using pyenv)

```bash
# Install pyenv if needed
brew install pyenv

# Install Python 3.11 and create venv
pyenv install 3.11.9
~/.pyenv/versions/3.11.9/bin/python -m venv .venv
source .venv/bin/activate
pip install build123d pytest
```

### Linux / Windows

```bash
# Ensure you have Python 3.10-3.12, then:
python3.11 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install build123d pytest
```

No package install step — runs as a plain Python module.

---

## Generate mold pieces

```bash
# Defaults (100 x 80 x 40 mm outer tray, output/ dir)
python -m hollow_idol

# Custom size
python -m hollow_idol --outer-x 120 --outer-y 100 --outer-z 50

# Specify printer for bed-size warnings, custom output dir, also export STEP
python -m hollow_idol --printer bambu-x1c --out-dir my_run/ --step
```

**Output files** (written to `--out-dir`):

```
half_a_wall_left.stl   half_a_wall_right.stl   half_a_bottom.stl
half_b_wall_left.stl   half_b_wall_right.stl   half_b_bottom.stl
```

Half A bottom has convex hemisphere keys and an ID notch. Half B bottom has concave divots.

---

## Test and verify

```bash
pytest tests/ -v                  # 51 geometry + dimension tests
python -m hollow_idol.reporter    # human-readable dimension check
```

The reporter accepts the geometry-sizing and fit-check flags shown below, plus `--json`,
and exits non-zero if any check fails.

---

## Parameters

| Flag | Default | Description |
|---|---|---|
| `--outer-x` | 100 mm | Outer tray width |
| `--outer-y` | 80 mm | Outer tray depth |
| `--outer-z` | 40 mm | Outer tray height |
| `--wall` | 5 mm | Wall and floor thickness |
| `--chamfer` | 3 mm | Interior corner chamfer size |
| `--hemi-r` | 6 mm | Registration key sphere radius |
| `--hemi-height` | 3 mm | Dome / divot height |
| `--hemi-offset` | 15 mm | Key centre distance from interior corner |
| `--tongue-clearance` | 0.25 mm | Panel fit clearance |
| `--flange-width` | 10 mm | Binder clip flange width |
| `--flange-thickness` | 3 mm | Flange thickness |
| `--printer` | `generic-200` | Printer preset for bed-size warnings |
| `--out-dir` | `output/` | Export directory |
| `--step` | off | Also export STEP files |

---

## Printer presets

| Key | Printer | Bed (X × Y × Z mm) |
|---|---|---|
| `generic-200` | Generic 200 mm | 200 × 200 × 200 |
| `prusa-mk4` | Prusa MK4 | 250 × 210 × 220 |
| `bambu-p1s` | Bambu P1S | 256 × 256 × 256 |
| `bambu-x1c` | Bambu X1C | 256 × 256 × 256 |

A warning is printed if any piece exceeds the selected bed dimensions.

---

## Workflow context

1. Print the 6 pieces in PETG (or resin)
2. Assemble the two C-frames around a clay form or blank; slide in the bottom panel
3. Pour plaster into the assembled case
4. Once set, disassemble — the plaster mold is ready for slip casting
5. Fired ceramic shrinks ~13%; scale the form up by 1.13 to compensate
